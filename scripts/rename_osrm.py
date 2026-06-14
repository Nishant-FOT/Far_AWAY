import os
p = 'osrm-data'
files = sorted(os.listdir(p))
renamed = []
for f in files:
    if f.startswith('chennai.osrm'):
        src = os.path.join(p, f)
        dst = os.path.join(p, f.replace('chennai', 'region'))
        os.replace(src, dst)
        renamed.append((f, os.path.basename(dst)))
print('Renamed:', renamed)
print('Current files:', [fn for fn in sorted(os.listdir(p)) if fn.startswith('region.osrm')])
