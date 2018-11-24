from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature
from cryptography.exceptions import InvalidTag
import json
import sys
import os

class SecurityClient:
    def __init__(self, serverPublicKeyPath):
        self.DH = {}
        self.clientKeys = {}
        self.clientSymmetricKeys = {}
        self.SymmetricKey = None
        self.serverNonce = None
        self.clientNonce = {}
        with open(serverPublicKeyPath, 'rb') as pubfile:
            self.serverPublicKey = serialization.load_pem_public_key(pubfile.read(),backend=default_backend())

    #Communication with server
    def initializeSecurity(self,path,BackupPath, username, password):
        self.username = username
        path += '-' + username + '.pem'
        BackupPath += '-' + username + '.pem'

        try:
            with open(path,"rb") as pem:
                try:
                    self.privateKey = serialization.load_pem_private_key(pem.read(),password=password,backend=default_backend())
                    self.publicKey = self.privateKey.public_key()
                    self.clientKeys[username] = self.publicKey
                    print('succesfully obtained key, path ' + path + ' pwd ' + password.decode())
                except ValueError:
                    try:
                        with open(BackupPath,"rb") as backup:
                            print("The key is corrupted but i have the backup")
                            backup_key = serialization.load_pem_private_key(backup.read(),password=password,backend=default_backend())
                            self.privateKey = backup_key
                            self.publicKey = self.privateKey.public_key()
                            self.clientKeys[username] = self.publicKey
                    except FileNotFoundError:
                        print("I don't have the backup,and the key is corrupted")
                        self.generate_key(path,BackupPath)
        except FileNotFoundError:
            try:
                with open(BackupPath,"rb") as backup,open (path,"wb") as pem:
                    print("I don't have the private key but i have the backup")
                    try:
                        backup_key = serialization.load_pem_private_key(backup.read(),password=password,backend=default_backend())
                        SerializedPrivateKey = backup_key.private_bytes(encoding=serialization.Encoding.PEM,format=serialization.PrivateFormat.PKCS8,encryption_algorithm=serialization.BestAvailableEncryption(b'ServerMPSprivatekey'))
                        self.privateKey = backup_key
                        self.publicKey = self.privateKey.public_key()
                        self.clientKeys[username] = self.publicKey
                        pem.write(SerializedPrivateKey)
                    except ValueError:
                        print("The backup is corrupted")
                        self.generate_key(path,BackupPath)
            except FileNotFoundError:
                print("We should not arrive here")


    def generate_key(self):
        self.privateKey = rsa.generate_private_key(public_exponent=65537,\
                                               key_size=2048,\
                                               backend=default_backend())
        self.publicKey = self.privateKey.public_key()
        #print(len(self.privateKey))
        #print(len(self.publicKey.public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo)))

    def RSAEncryptText(self,text, key):
        #print('len mes:' + str(len(text)))
        cipherText = key.encrypt(text,
                                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                             algorithm=hashes.SHA256(),
                                             label=None
                                             )
                                 )
        return cipherText

    def getDigest(self,textBit):
        h = hashes.Hash(hashes.SHA256(), backend=default_backend())
        h.update(textBit)
        return h.finalize()

    def RSADecryptText(self,cipherText):
        plaintext = self.privateKey.decrypt(cipherText,
                                            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                         algorithm=hashes.SHA256(),
                                                         label=None
                                                         )
                                            )
        return plaintext

    def getSignature(self,text):
        try:
            signature = self.privateKey.sign(text,
                                         padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                     salt_length=padding.PSS.MAX_LENGTH
                                                     ),
                                         hashes.SHA256()
                                         )
            return signature
        except Exception as e:
            print(e)
            return None

    def VerifySignature(self,text,signature, user=None):
        try:
            if user is None:
                self.serverPublicKey.verify(signature,text,padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256())
            else:
                print('verifying the signature with the of ' + user)
                print('key : \n\n\n\n\n' + str(int.from_bytes(self.clientKeys[user].public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo), byteorder='big')))
                print(self.clientKeys[user].public_bytes(
                                                encoding=serialization.Encoding.PEM,
                                                format=serialization.PublicFormat.SubjectPublicKeyInfo)
                                                )
                self.clientKeys[user].verify(signature,text,padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256())
            return True
        except InvalidSignature as e:
            print('firma errata')
            return False

    def getServerPublicKey(self):
        return self.serverPublicKey.public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo)

    def getSerializedPublicKey(self):
        return self.publicKey.public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo)

    def AddSymmetricKeyFromDict(self,dict):
        """Must be passed as argument the dict located at message['key']"""
        #self.len = int(key["lenght"])
        #self.SymmetricKey = struct.pack("B"*int(dict["lenght"]/8),*dict["content"])
        print('chiave? ' + str(dict))
        self.SymmetricKey = dict.to_bytes(16, byteorder='big')

    def getSymmetricKey(self):
        return self.SymmetricKey;

    def AESDecryptText(self,ct,username = None, nonce = None):
        try:
            if nonce is not None:
                aescgm = AESGCM(self.SymmetricKey)
                if username is None:
                    self.serverNonce = self.serverNonce+1
                    print('decryptnonceserver ' + str(self.serverNonce))
                    return aescgm.decrypt(self.serverNonce.to_bytes(16, byteorder="big"),ct,None)
                else:
                    self.clientNonce[username] = self.clientNonce[username]+1
                    print('decryptnonceserver ' + str(self.clientNonce[username]))
                    return aescgm.decrypt(self.clientNonce[username].to_bytes(16, byteorder="big"),ct,None)
            else:
                aescgm = AESGCM(self.clientSymmetricKeys[username])
                self.clientNonce[username] = self.clientNonce[username]+1
                print('decryptnonceclient ' + str(self.clientNonce[username]))
                return aescgm.decrypt(self.clientNonce[username].to_bytes(16, byteorder="big"),ct,None)
        except TypeError as t:
            print(t)
            print("Error in decrypt GCM")
            return None
        except:
            print(sys.exc_info()[0])
            return 'NOPE'

    def AESEncryptText(self,pt, username = None):
        try:
            if username is None:
                print(self.serverNonce)
                aesgcm = AESGCM(self.SymmetricKey)
                self.serverNonce = self.serverNonce+1
                #print('encryptnonce ' + str(self.serverNonce))
                return aesgcm.encrypt(self.serverNonce.to_bytes(16, byteorder="big"), pt, None)
            else:
                aesgcm = AESGCM(self.clientSymmetricKeys[username])
                self.clientNonce[username] = self.clientNonce[username]+1
                print('Nonce client used for AES encrypt ' + str(self.clientNonce[username]))
                #print('encryptnonce ' + str(self.serverNonce))
                return aesgcm.encrypt(self.clientNonce[username].to_bytes(16, byteorder="big"), pt, None)

        except Exception as e:
            print(e)
            print("Error in encrypt GCM")
            return None

    def decryptText(self, text):
        msg = b''
        if self.SymmetricKey is None:
            #print(len(text[0:-1025]))
            sign = text[-1025:]
            msg = self.RSADecryptText(text[0:-1025])
            if self.VerifySignature(msg, sign):
                return msg
            else:
                None
        else:
            return self.AESDecryptText(text, None, 1)


    def savePrivateKey(self, path, backupPath, password):
        with open(path,"wb") as pem, open(backupPath,"wb") as backup:
            print("saving the keys")
            serializedPrivateKey = self.privateKey.private_bytes(
                                            encoding=serialization.Encoding.PEM,
                                            format=serialization.PrivateFormat.PKCS8,
                                            encryption_algorithm =serialization.BestAvailableEncryption(
                                                password.encode('utf-8')
                                                )
                                            )
            pem.write(serializedPrivateKey)
            backup.write(serializedPrivateKey)

    '''
        Methods to establish a secure communication client to client
        using Diffie-Hellman
    '''
    def generateDHParameters(self):
        '''
        generates the parameters g and p, these are public and can be reused
        '''
        print('generate parameters')
        self.parameters = dh.generate_parameters(
                                            generator=2,
                                            key_size=512,
                                            backend=default_backend()
                                            )
        self.parnum = self.parameters.parameter_numbers()
        print('g: ' + str(self.parnum.g) + ' p:' + str(self.parnum.p))
        return [self.parnum.g, self.parnum.p]

    def saveParameters(self,g,p, path):
        txt = {}
        txt['g'] = g
        txt['p'] = p
        with open(path+'json', 'w') as parameters:
            json.dump(txt, parameters)

    def loadParameters(self, path):
        par = {}
        with open(path+'-'+self.username+'.json', 'r') as parameters:
            par = json.loads(parameters.read())
        self.generateDH(par['p'], par['g'], self.username)

    def resetKeys(self):
        self.privateKey = None
        self.publicKey = None

    def generateDH(self, p, g, user):
        pn = dh.DHParameterNumbers(int(p), int(g))
        self.parameters = pn.parameters(default_backend())
        #print('g^a mod p')
        self.DH[user] = self.parameters.generate_private_key()


#    def computeDHtoSend(self, user):
#        return self.DH[user]

    def computeDHKey(self, user, shared_key):
        '''
            We must pass the value g^b mod p = shared_key received by the other client
            and compute the key as (g^b mod p)^a mod p
            when we compute this we remove from the system
        '''
        print('key of the communication with the other host has been computed')
        self.clientSymmetricKeys[user] = HKDF(
                 algorithm=hashes.SHA256(),
                 length=32,
                 salt=None,
                 info=b'handshake data',
                 backend=default_backend()
            ).derive(shared_key)
        print('added symmetric key')
        print(self.clientSymmetricKeys[user])

    def getSharedKey(self, user):
        return self.DH[user].exchange(self.DH[user].public_key())

    def insertKeyClient(self, user, key):
        print('inserting the key of ' + user)
        print(key)
        self.clientKeys[user] = serialization.load_pem_public_key(key.encode('utf-8'),backend=default_backend())

    def insertSymmetricKeyClient(self, user, key):
        self.clientSymmetricKeys[user] = serialization.load_pem_public_key(key.encode('utf-8'),backend=default_backend())

    def getKeyClient(self, user):
        return self.clientKeys[user]

    def addClientNonce(self, user, nonce):
        self.clientNonce[user] = nonce

    def getClientNonce(self, user):
        return self.clientNonce[user]

    def generateNonce(self,size):
        """ Generate a nonce of a dimension chosed (in bytes) a get it as an Integer encoded in Big Endian
            Parameter:
                    size: The size (in Bytes) of the nonce                                                                          : int
            Return:
                    A nonce generated using the system call specific for cryptography purpose of the dimensione passed as argument  : int """
        return int.from_bytes(os.urandom(size),byteorder='big')
