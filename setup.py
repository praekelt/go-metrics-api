from setuptools import setup, find_packages

setup(
    name="go-metrics-api",
    version="0.1.7a",
    url='http://github.com/praekelt/go-metrics-api',
    license='BSD',
    description="An API for querying vumi-go metrics",
    long_description=open('README.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekeltfoundation.org',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'treq',
        'cyclone',
        'go_api>=0.2.0',
        'confmodel==0.2.0',
        'vumi>=0.5.21',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
