from setuptools import setup, find_packages

setup(
    name='OpenRoute',
    keywords=['routing optimization'],
    description='An open source route optimization tool based on Google ortool.',
    py_modules=['manage'],
    install_requires=['ortools', 'pandas', 'requests', 'coverage', 'shapely', 'xlrd', 'Click', 'openpyxl'],
    entry_points='''
        [console_scripts]
        routing=manage:cli
    ''',
    license='Apache License 2.0',
    version='0.0.1',
    author='ccwukong',
    author_email='ccwukong@gmail.com',
    packages=find_packages(),
    platforms='any',
)
