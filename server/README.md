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
