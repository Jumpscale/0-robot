# Security

## REST API authentication schemes
The 0-robot REST API has 3 level of authentication and each level gives access to a part of the API.  
You **MUST** run the 0-robot API behind HTTPS, failing to do so would allow hackers to gather your secrets and usurp your identity

### Admin level:
This level of authentication give you access to all the API. Specifically it allows the admin to call the `add_repo` and `checkout_repo` endpoint. These endpoint need to be protected cause they allow to bring new code in the robot.

To authenticate as an admin, request needs to be Authenticated with a JWT given from [ItYouOnline](https://itsyou.online/) and contains the scope: `user:memberof:<org>` where `<org>` is the value of the `--admin-organization` flag given to the `zrobot server start` command. In case this flag is not passed, the `add_repo` and `checkout_repo` methods are open to anyone.

JWT need to be set in the `ZrobotAdmin` header of the HTTP request, like so:  
```
ZrobotAdmin: Bearer <token>
````

### User level:  
This is the normal level of authentication. It cover all the method to create/list services.

Request needs to be Authenticated with a JWT given from [ItYouOnline](https://itsyou.online/) and contains the scope: `user:memberof:<org>` where `<org>` is the value of the `--user-organization` flag given to the `zrobot server start` command. In case this flag is not passed, the api methods are open to anyone.

JWT need to be set in the `ZrobotUser` header of the HTTP request, like so:  
```
ZrobotUser: Bearer <token>
````

### Service level:
The part of the API that deals with scheduling actions on a service is protected with a secret that is returned to the client that created a service.  The goal is to only allow the client that created the service to be able to schedule actions on the service.

All the secret you got from the same robot need to be set in the `ZrobotSecret` header of the HTTP request, like so:
```
ZrobotSecret: Bearer <token> <token> <token> ...
````
**note**: `list services` method of the API, will only returns the services for which you have access and not all the services from the robot.

#### Matrix of API methods to authentication level:

| method | level |
|---|---|
|create service         |admin, user|
|add template repo      |admin|
|checkout template repo  |admin|
|list services          |admin, user, service|
|list templates         |admin, user, service|
|add task to task list  |service|
|delete service         |admin, user, service|
|execute blueprint      |admin, user, service|
|get service            |service|
|get task               |service|
|list tasks             |service|
|list actions           |service|


## God mode:
god mode allows you to access functionalities with no need to go through the security schema.
First:
Start the robot with god mode flag 
### example:
```bash
zrobot server start -T http://github.com/zero-os/0-templates --god
```
Then get god token from robot to be able to access functionalities

```bash
zrobot godtoken get
```
then using Jumpscale
set god token in client configurations 
```bash
cl = j.clients.zrobot.get('instance_name')
cl.god_token_set('god_token")
```
Note: to access functionalities of the robot .. must god mode flag is true and you must provide the correct god token