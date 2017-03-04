#!/usr/bin/env python
# encoding: utf-8
from flask import jsonify
from  werkzeug.wrappers import Response



class JSONResponse(Response):
    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv,dict):
            rv=jsonify(rv)
        return super(JSONResponse,cls).force_type(rv,environ)


