from setuptools import setup, find_packages

setup(
    name='ZeroRobot',
    version='0.0.1',
    description='Automation framework for cloud workloads',
    url='https://github.com/Jumpscale/zerorobot',
    author='GreenItGlobe',
    author_email='info@gig.tech',
    license='Apache',
    packages=find_packages(),
    include_package_data=True,
    package_data={'zerorobot': ['api/schema/*.json', 'api/index.html', 'api/apidocs/*', 'api/apidocs/*/*']},
    install_requires=[
        'JumpScale9',
        'JumpScale9Lib',
        'gevent>=1.2.2',
        'Flask==0.10.1',
        'Flask-Inputs==0.2.0',
        'Jinja2==2.8',
        'MarkupSafe==0.23',
        'Werkzeug==0.11.4',
        'itsdangerous==0.24',
        'jsonschema==2.5.1',
        'six==1.10.0',
        'python-jose==1.3.2',
    ],
    scripts=['cmd/zrobot']
)
