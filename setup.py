from setuptools import setup, find_packages

setup(
    name='django-ua-mapper',
    version='0.0.1',
    description='Django app mapping User-Agent header strings to settings modules via Redis.',
    long_description = open('README.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekelt.com',
    license='BSD',
    url='https://github.com/praekelt/django-ua-mapper',
    packages = find_packages(),
    include_package_data=True,
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    install_requires = [
        'redis',
        'pywurfl',
    ],
    zip_safe=False,
)
