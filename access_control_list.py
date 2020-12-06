import json

class ACL:

    def __init__(self):
        self.rules = list()
        self.newRules = list()
        self.loadRules()

    def newRule(self,username,path,permissions):
        rule = {"username":username,"path":path,"permissions":permissions}
        self.newRules.append(rule)

    def printRules(self):
        print("\nCurrent ACL Rules\n-----------------")
        for rule in self.rules:
            print(rule)

    def removeRule(self, username, path, permissions):  
        rule = {"username":username,"path":path,"permissions":permissions}
        self.newRules.remove(rule)
        return True

    def loadRules(self):
        with open("aclRules.json","r") as aclFile:
            self.rules.clear()
            self.newRules.clear()
            rules = json.load(aclFile)
            for rule in rules:
                self.rules.append(rule)
                self.newRules.append(rule)
            aclFile.close()
            return True
        return False

    def check(self,username,path):
        #print("Checking... ",path)
        if path == "/home/student/fuse/":
            return "2"
        for rule in self.rules:
            if rule["username"] == username and path.rfind(rule["path"]) > -1:
                #print("--ACL\t",rule["permissions"])
                return rule["permissions"]
        return "0"

    def writeRules(self):
        with open("aclRules.json","w") as aclFile:
            #self.rules.extend(self.newRules)
            #self.printRules()
            aclFile.seek(0)
            json.dump(self.newRules,aclFile)
            aclFile.close()

    def __del__(self):
        self.writeRules()
        print("deleting acl")

def main():
    acl = ACL()
    acl.printRules()
    
    acl.newRule("admin","/home/student/fuse",2) #user admin can do whatever they want to
    acl.newRule("trusted","/home/student/fuse/config",0) #user trusted cannot read from or write to config
    acl.newRule("trusted","/home/student/fuse",2) #otherwise user trussted can do whatever they want to
    acl.newRule("public","/home/student/fuse/config",0)
    acl.newRule("public","/home/student/fuse/trusted",0)
    acl.newRule("public","/home/student/fuse/public",1) #user public can read from public and do nothing else
    acl.newRule("carter","/home/student/fuse",2)
    acl.writeRules()
    acl.loadRules()
    print(acl.check("admin","/home/student/fuse"))
    print(acl.check("admin","/home/student/fuse/middle"))
    print(acl.check("public","/home/student/fuse/public"))
    print(acl.check("public","/home/student/fuse/config"))
    print(acl.check("trusted","/home/student/fuse/trusted"))
    print(acl.check("trusted","/home/student/fuse/config"))
    print(acl.check("trusted","/home/student/fuse/middle"))
    
    acl.removeRule("carter","/home/student/fuse",2)
    acl.writeRules()
    acl.loadRules()
    print(acl.newRules)
    acl.printRules()

#main()
