# Feaders Server
Feaders server component can perform lookup of hundreds of files in a fraction of a second.
This is in stark contrast with `repoquery` which takes roughly *100x more time* to do the same search.
The speed is achieved by directly querying the repository database that is obtained as `sqlite` files.
Two queries are necessary to search for a single file, both execute in the range of 500us-10ms, depending
on the cache locality.
This makes the reply almost instantenous even for large projects.

### Usage

To start the server simply execute the `feaders-server` executable.

```bash
$ ./feaders-server
 * Running on http://127.0.0.1:5000/
 * Restarting with reloader
```

Note that repository caches are saved in the current working directory. 

Now simply add some repositories via the web interface at `localhost:5000/add_cache` or by issuing a curl query:

```bash
$ curl 'localhost:5000/refresh_cache?arch=x86_64&name=fedora&release=23&type=fedora'
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to target URL: <a href="/">/</a>.  If not click the link.
```

### Comparison

`nokogiri` with and without server :

```
real    0m1.306s
user    0m0.923s
sys     0m0.045s

real    3m48.845s
user    3m9.854s
sys     0m17.853s
```

`Pillow` with and without server :

```
real    0m1.225s
user    0m0.945s
sys     0m0.040s

real    1m43.552s
user    1m31.689s
sys     0m8.492s
```
