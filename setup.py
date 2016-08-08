#!/usr/bin/env python


from setuptools import setup

setup(name='boto3_wrapper',
      version='0.1',
      description='A wrapper for boto3, that is IDE friendly and more',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.0',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development :: Libraries',
      ],
      url='https://github.com/fivestars/boto3_wrapper',
      author='Fivestars',
      license='MIT',
      packages=['boto3_wrapper'],
      install_requires=[
          'boto3==1.4.0',
      ],
      include_package_data=True,
      zip_safe=True)
