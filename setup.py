import setuptools

setuptools.setup(
    name='phf',
    version='1.0.0',
    packages=['phf'],
    install_requires=["aioconsole", "aiofiles", "aiohttp"],
    package_dir={'phf': 'phf'},
    url='https://github.com/framaz/phf',
    license='MIT License',
    author='framaz',
    author_email='framaz@yandex.ru',
    description='Async framework.',
    python_requires='>=3.5',
)
