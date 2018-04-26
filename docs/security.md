# Security

## REST API authentication schemes
The 0-robot REST API has 2 schemes of authentication and each scheme gives access to a part of the API.

### Organization secret:  
Request needs to be Authenticated with a JWT given from [ItYouOnline](https://itsyou.online/) and contains the scope: `user:memberof:<org>` where `<org>` is the value of the `--organization` flag given to the `zrobot server start` command. In case this flag is not passed, the api methods are open to anyone.

JWT need to be set in the `Authorization` header of the HTTP request, like so:  
```
Authorization: Bearer <token>
````

### User Secret:
The part of the API that deals with services is protected with a secret that is returned to the client that created a service.  The goal is to only allow the client that created the service to be able to schedule actions on the service.

All the secret you got from the same robot need to be set in the `Zrobot` header of the HTTP request, like so:
```
Zrobot: Bearer <token> <token> <token> ...
````
**note**: `list services` method of the API, will only returns the services for which you have access and not all the services from the robot.

#### Matrix of API methods to authentication scheme:

| method | scheme |
|---|---|
|create service         |organization|
|add template repo      |organization|
|checkout template repo  |organization|
|list services          |organization|
|list templates         |organization|
|add task to task list  |user|
|delete service         |organization, user|
|execute blueprint      |organization|
|get service            |organization, user|
|get task               |user|
|list tasks             |user|
|list actions           |user|
