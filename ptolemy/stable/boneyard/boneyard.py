def compute_dir_digest(path):
    hash = sha.new()
    time = 0

    for dpath, dnames, fnames in os.walk(path):
        dinfo = os.stat(dpath)
        hash.update(dpath)
        # We ignore dir change times
        #time = max(time, dinfo[stat.ST_MTIME], dinfo[stat.ST_CTIME])

        for fname in fnames:
            fpath = os.path.join(dpath, fname)

            try:
                finfo = os.stat(fpath)
                hash.update(fpath)
                time = max(time, finfo[stat.ST_MTIME], finfo[stat.ST_CTIME])
            except OSError:
                pass
            
        for dname in (".svn", "CVS"):
            if dname in dnames:
                dnames.remove(dname)

    return hash.hexdigest() + " " + str(time)
