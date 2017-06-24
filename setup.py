from setuptools import setup

import serdepa

setup(name='serdepa',
      version=serdepa.version,
      description='Binary packet serialization and deserialization library.',
      url='https://github.com/thinnect/serdepa',
      author='Raido Pahtma, Kaarel Ratas',
      author_email='github@thinnect.com',
      license='MIT',
      packages=['serdepa'],
      install_requires=['six'],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
