# Service versioning

The version of a service is actually the version of the template used to create it.
When you create a service, you need to specify which template to use. By default the robot will always use the higher version possible of the template if multiple version of the same template is loaded in the robot.

## Upgrade a service
When you load new template version in the robot, all the services created from these templates will be upgraded to the newer version of the template.

Example:
```python
# here we pull the template repo and checkout the tag 2.0.0
robot.templates.checkout_repo('https://github.com/zero-os/0-templates','2.0.0')
```

Another possibility of upgrade of service, is if you stop the robot, upgrade the template version and then restart the robot. During bootstrap, the robot will try to upgrade the service to the latest version available of the templates.