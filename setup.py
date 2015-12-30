from setuptools import setup

setup(
    zip_safe=True,
    name='yttc',
    version='1.0',
    packages=[
        'yttc',
        'yttc/plugin'
    ],
    license='Apache License',
    description='Library for convert from YANG to cloudify TOSCA',
    install_requires=[
        'pyang',
        'pyaml'
    ],
    entry_points='''
        [console_scripts]
        yttc=yttc.wrapper:cli
    '''
)
