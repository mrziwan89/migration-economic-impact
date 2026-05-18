const fs = require("fs");
const http = require("http");
const path = require("path");

const port = Number(process.argv[2] || 5174);
const root = process.cwd();
const types = {
  ".html": "text/html; charset=utf-8",
  ".csv": "text/csv; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8"
};

const server = http.createServer((req, res) => {
  let pathname = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
  if (pathname === "/") {
    pathname = "/index.html";
  }

  const file = path.resolve(root, `.${pathname}`);
  if (!file.startsWith(root)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.stat(file, (err, stat) => {
    if (err || !stat.isFile()) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }

    res.writeHead(200, {"Content-Type": types[path.extname(file)] || "application/octet-stream"});
    fs.createReadStream(file).pipe(res);
  });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Serving ${root} at http://localhost:${port}/`);
});
