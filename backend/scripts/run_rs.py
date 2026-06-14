import importlib.util
spec=importlib.util.spec_from_file_location('replay_store','/app/app/services/replay_store.py')
rs=importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)
print('DB_PATH=', rs.DB_PATH)
print('stages for delhi_flood_001:', rs.get_stages('delhi_flood_001'))
