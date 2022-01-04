from distutils.core import setup

setup(name='caretaker_fdata',
      version='1.0',
      packages=['src'],
      # Start with a small number and increase it with every change you make
      license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
      description = 'finance management tool',   # Give a short description about your library
      author = 'Dan',                   # Type in your name
      author_email = 'daniel.js.campbell@gmail.com',      # Type in your E-Mail
      url = 'https://github.com/dn757657/caretaker_f2',   # Provide either the link to your github or to your website
      download_url = 'https://github.com/dn757657/caretaker_f2/archive/refs/tags/testing.tar.gz',    # I explain this later on
      keywords = ['Management', 'finance', 'automation'],   # Keywords that define your package best
      install_requires=[            # I get to this in a second
            'pandas',
            'tabulate',
            'web3',
            'python-dateutil',
            'textblob',
            'colorama',
            'docopt',
            'qtrade',
            'pandas_datareader',
            'textblob',
      ],
      classifiers=[
            'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
            'Intended Audience :: Developers',      # Define that your audience are developers
            'Topic :: Software Development :: Build Tools',
            'License :: OSI Approved :: MIT License',   # Again, pick a license
            'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
      ],
      )