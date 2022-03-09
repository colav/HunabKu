from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
import pandas as pd
import os
import sys


class Scienti(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    @endpoint('/scienti/product', methods=['GET'])
    def scienti_query(self):
        """
        @api {get} /scienti/product Scienti prouduct endpoint
        @apiName Query
        @apiGroup Scienti
        @apiDescription Allows to perform queries for products, 
                        model_year is mandatory parameter, if model year is the only 
                        parameter passed, the endpoint returns all the dump of the database. 

        @apiParam {String} apikey  Credential for authentication
        @apiParam {String} COD_RH  User primary key
        @apiParam {String} COD_PRODUCTO  product key (require COD_RH)
        @apiParam {String} SGL_CATEGORIA  category of the product
        @apiParam {String} model_year  year of the scienti model, example: 2018
        
        @apiSuccess {Object}  Resgisters from MongoDB in Json format.

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 400) msg  Bad request, if the query is not right.

        @apiExample {curl} Example usage:
            # all the products for the user
            curl -i http://hunabku.server/scienti/product?apikey=XXXX&model_year=2018&COD_RH=0000000639
            # An specific product
            curl -i http://hunabku.server/scienti/product?apikey=XXXX&model_year=2018&COD_RH=0000000639&COD_PRODUCTO=24
            # all the products (use this with carefull, it is a lot of info and pagination is not supported yet)
            curl -i http://hunabku.server/scienti/product?apikey=XXXX&model_year=2018
        """

        if self.valid_apikey():
            query = self.request.args.get('query')
            cod_rh = self.request.args.get('COD_RH')
            cod_prod = self.request.args.get('COD_PRODUCTO')
            sgl_cat = self.request.args.get('SGL_CATEGORIA')
            model_year = self.request.args.get('model_year')
            
            try:
                if model_year:
                    db_name = f'scienti_{model_year}'
                    db_names = self.dbclient.list_database_names()
                    if db_name in db_names:
                        self.db = self.dbclient[db_name]
                        data=[]
                        if cod_rh and cod_prod:
                            print({'COD_RH': cod_rh, 'COD_PRODUCTO': cod_prod})
                            data = self.db["product"].find_one({'COD_RH': cod_rh, 'COD_PRODUCTO': cod_prod},{"_id":0})
                            print(data)
                            response = self.app.response_class(
                                response=self.json.dumps(data),
                                status=200,
                                mimetype='application/json'
                            )
                            return response
                        elif cod_rh:
                            data = list(self.db["product"].find({'COD_RH': cod_rh},{"_id":0}))
                            response = self.app.response_class(
                                response=self.json.dumps(data),
                                status=200,
                                mimetype='application/json'
                            )
                            return response
                        if sgl_cat:
                            data = list(self.db["product"].find({'SGL_CATEGORIA': sgl_cat},{"_id":0}))
                            response = self.app.response_class(
                                response=self.json.dumps(data),
                                status=200,
                                mimetype='application/json'
                            )
                            return response

                        data = list(self.db["product"].find({},{"_id":0}))
                        response = self.app.response_class(
                            response=self.json.dumps(data),
                            status=200,
                            mimetype='application/json'
                        )
                        return response

                    else:
                        #database for model year not found
                        data = {"error": "Bad Request", "message": "invalid model_year, database not found for the given year {model_year}"}
                        response = self.app.response_class(
                            response=self.json.dumps(data),
                            status=400,
                            mimetype='application/json'
                        )
                        return response
                else:
                    #model year required
                    data = {"error": "Bad Request", "message": "model_year parameter is required, it was not provided."}
                    response = self.app.response_class(
                        response=self.json.dumps(data),
                        status=400,
                        mimetype='application/json'
                    )
                    return response
            except:
                data = {"error": "Bad Request", "message": str(sys.exc_info())}
                response = self.app.response_class(
                    response=self.json.dumps(data),
                    status=400,
                    mimetype='application/json'
                )
                return response
        else:
            return self.apikey_error()

