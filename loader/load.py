import os
import datetime
import subprocess
import psycopg2
import click
from pathlib import Path

DATA_DIRECTORY = '/data/'

class CsvLoader():
    """
    Contains some methods to manipulate or load data.
    """

    # find new csv's to import in the raw_data folder
    def find_new_data(self):
        dirpath = Path(DATA_DIRECTORY)
        assert dirpath.is_dir()
        file_list = []
        for x in dirpath.iterdir():
            if x.is_file():
                file_list.append(x)
        return file_list

    def load_data(self):
        file_list = self.find_new_data()
        for file in file_list:
            filename = file.name
            table_name = filename[:-4].replace('-','_') # remove extension and hyphens
            click.echo(f"Starting to load {filename}.")
            cmd = f'csvsql --db postgresql://postgres:postgres@db --insert --overwrite --chunk-size 100 --tables {table_name} -v -y 2048 {file}' #enabled overwrite to allow dataset updates
            run = subprocess.run(cmd, capture_output=True, shell=True)

            # If we had a non-0 return code.
            if run.returncode:
                raise Exception(f'csvsql exception:', run.stdout, run.stderr)
            else:
                click.echo("Loaded")
                click.echo(run.stdout)

            # move the processed file to the loaded folder - disabled for testing purposes
            # now = datetime.datetime.now()
            # os.replace(file, DATA_DIRECTORY + 'loaded/' + filename[:-4] + '_' + now.strftime('%Y%m%d_%H%M%S') + '.csv')

@click.command()
def load():
    """Simple program to load files into our DB."""
    click.echo(f"Loading data sets!")
    CsvLoader().load_data()
    click.echo("All Done!")


if __name__ == '__main__':
    load()
