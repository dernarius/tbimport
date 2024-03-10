install with `pip install -e .`

to use:
* create a new directory somewhere else
* create a settings.yaml file which should look roughly like this:

```yaml
host: https://tab.pikta.lt/  # domain for the tabbycat instance
apikey: aaaaaaaaaaaaa  # superuser api key
slug: slug2024  # tournament slug
break_category_id: 1  # id for the open break category
```

break_category_id is necessary so that all teams would be added to the open break category

* prepare judges.csv and teams.csv input files
* run `tbimport ensure-institutions` - this will create any institutions necessary for the input files
* run `tbimport import-judges`
* run `tbimport import-teams`
* clean up any messes created by the last two commands
