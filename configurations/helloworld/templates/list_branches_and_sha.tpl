% import time
<h1>Binocular - list of branches and demos</h1>
%for branch in branches:
    <h2>{{branch['name']}}!</h2>
%for sha in branch['shas']:
      <p>
      <svg height="10" width="10"><circle cx="5" cy="5" r="4" fill="{{'red' if sha['status'] == 'failed' else 'green' if sha['status'] == 'success' else 'yellow'}}"><title>{{sha['status']}}</title></circle></svg>
      {{time.ctime(sha['date'])}}
%if sha['status'] == 'success':
        <a href="branches/{{branch['name']}}/{{sha['name']}}/index.html">demo (change this URL)</a>
%end
        <a href="status/{{branch['name']}}/{{sha['name']}}">logs</a>
      </p>
%end
