import nbformat, os, sys, time
os.environ["NB_BATCH"] = "1"   # tuning panels render their default result directly (see nb_tuning.py)
from nbclient import NotebookClient
p = sys.argv[1]
nb = nbformat.read(p, as_version=4)
t0 = time.time()
c = NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(__import__('pathlib').Path(p).parent)}})
try:
    c.execute()
    print("OK in", round(time.time()-t0), "s")
finally:
    nbformat.write(nb, p)
