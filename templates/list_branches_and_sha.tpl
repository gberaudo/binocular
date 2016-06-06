% import time
%for branch in branches:
    <h1>Branch {{branch['name']}}!</h1>
%for sha in branch['shas']:
      <p> {{time.ctime(sha['date'])}}
        <a href="branches/{{branch['name']}}/{{sha['name']}}/dist/examples/index.html">demo</a>
        <a href="status/{{branch['name']}}/{{sha['name']}}">logs</a>
      </p>
%end
