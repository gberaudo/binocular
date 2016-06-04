#!/bin/sh

owner=`stat -c '%u:%g' .git`

chown -R nonroot:nonroot .
su nonroot -c "make dist; make check; make dist-examples; make dist-apidoc"
chown -R $owner .
