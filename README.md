# LUNA16 Challenge Dataset

## Instructions

Clone this repo and move the [**LUNA16**](https://luna16.grand-challenge.org/) dataset to such directory, will look like that:

```
\--LUNA16-Image-Extractor
 |
 |--/CSVFILES
 |--/subset0
 |--/subset1
 .
 .
 .
 |--README.md
 |--Pipfile
 |--Pipfile.lock
 |--requirements.txt
```

 **WARNING**:
Maybe happen with you some trouble with the dataset unpacking, to run around that:
```bash
zip -FFv subset_some_number.zip --out fixed_compressed_file.zip
```
and then:
```bash
unzip fixed_compressed_file.zip
```


If you are using **pipev**:
```bash
pipenv install
```
if isn't:
```bash
pip install -r requirements.txt
```
