# gaia-clustering Readme

The codes contains two folder
* Src: Which contains some basic Apis which can called to realise different features.
* Test: Some demos including converting from nt file to json cluster head file for both entities and events and clustering


Order of running:
- Entitiy: 
  1. from_AIF_to_JSON_head.py 
  2. from_jsonhead2cluster.py
- Event: 
  1. extract_event_cluster.py 
  2. baseline2.exe.py

If uri is changed, please modify
- /src/change_type_for_multi_file.py 
- /test/from_AIF_to_JSON_head.py 
- /src/event_baseline2.py 