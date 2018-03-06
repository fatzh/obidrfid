from distutils.core import setup
setup(
    name='obidrfid',
    py_modules=['obidrfid'],
    scripts=['obidrfid.py'],
    version='0.8',
    description='Python wrapper to communicate with eh OBID RFID IP antennas',
    author='Fabrice Tereszkiewicz',
    author_email='fabrice.tz@51stfloor.com',
    url='https://github.com/fatzh/obidrfid',
    download_url='https://github.com/fatzh/obidrfid/archive/0.8.tar.gz',
    keywords=['rfid', 'obid'],
    classifiers=[],
)
