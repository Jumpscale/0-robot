# Security

## REST API authentication schemes
The 0-robot REST API has 2 schemes of authentication and each scheme gives access to a part of the API.

### Admin/Management:  
Request needs to be Authenticated with a JWT given from [ItYouOnline](https://itsyou.online/) and contains the scope: `user:memberof:<org>` where `<org>` is the value of the `--organization` flag given to the `zrobot server start` command. In case this flag is not passed, the admin methods are open to anyone.

JWT need to be set in the `Authorization` header of the HTTP request, like so:  
```
Authorization: Bearer <token>
````

### User Secret:
The part of the API that deals with services is protected with a secret that is return to the client that created a service.  The goal is to only allow the client that created the service to be able to schedule actions on the service.

JWT need to be set in the `Authorization` header of the HTTP request, like so:  
```
Authorization: ZrobotAuth <token>
````


Matrix of API methods to authentication scheme:

| method | scheme |
|---|---|
|create service         |admin|
|add template repo      |admin|
|checout template repo  |admin|
|list services          |admin|
|list templates         |admin|
|add task to task list  |user|
|delete service         |admin, user|
|execute blueprint      |admin|
|get service            |multi|
|get task               |user|
|list tasks             |user|
|list actions           |user|