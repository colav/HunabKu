from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
import pandas as pd
import cx_Oracle
import os
import sys


class Scienti(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)
        envs = ["CVLAC_USER", "GRUPLAC_USER", "INSTITULAC_USER", "ORACLE_PWD"]
        for var in envs:
            if var not in os.environ:
                print(f"Error: {var} not defined in the environment.")
                sys.exit(1)

        self.CVLAC_USER = os.environ["CVLAC_USER"]
        self.GRUPLAC_USER = os.environ["GRUPLAC_USER"]
        self.INSTITULAC_USER = os.environ["INSTITULAC_USER"]
        ORACLE_PWD = os.environ["ORACLE_PWD"]
        self.oracle_db = cx_Oracle.connect(
            user="system",
            password=ORACLE_PWD,
            dsn="localhost:1521")
        self.cvlac_tables = pd.read_sql(
            f"SELECT * FROM all_tables WHERE OWNER='{self.CVLAC_USER}'", con=self.oracle_db)["TABLE_NAME"].values.tolist()
        self.grublac_tables = pd.read_sql(
            f"SELECT * FROM all_tables WHERE OWNER='{self.GRUPLAC_USER}'", con=self.oracle_db)["TABLE_NAME"].values.tolist()
        self.institulac_tables = pd.read_sql(
            f"SELECT * FROM all_tables WHERE OWNER='{self.INSTITULAC_USER}'", con=self.oracle_db)["TABLE_NAME"].values.tolist()

    def rename_duplicate_cols(sefl, df):
        cols = pd.Series(df.columns)
        # https://stackoverflow.com/questions/24685012/pandas-dataframe-renaming-multiple-identically-named-columns
        for dup in df.columns[df.columns.duplicated(keep=False)]:
            cols[df.columns.get_loc(dup)] = ([dup + '.' + str(d_idx)
                                              if d_idx != 0
                                              else dup
                                              for d_idx in range(df.columns.get_loc(dup).sum())]
                                             )
        df.columns = cols
        return df

    @endpoint('/scienti/query', methods=['GET'])
    def scienti_query(self):
        """
        @api {get} /scienti/query Scienti query endpoint
        @apiName Query
        @apiGroup Scienti
        @apiDescription Allows to perform any query to the db, but the query have to have the right db name, table name and relationship.
                        you can see dbs and tables on the endpoint info

        @apiParam {String} apikey  Credential for authentication
        @apiParam {String} request  SQL query
        @apiParam {String} orient  data orientation "split or records", default records (More common but more expensive in memory)
        @apiSuccess {Object}  Resgisters from OracleDB in Json format.

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 400) msg  Bad request, if the query is not right.
        """

        if self.valid_apikey():
            query = self.request.args.get('request')
            orient = self.request.args.get('orient')
            if orient is None:
                orient = "records"
            try:
                df = pd.read_sql(query, con=self.oracle_db)
                if orient == "records":
                    df = self.rename_duplicate_cols(df)
                data = df.to_json(orient=orient)
                response = self.app.response_class(
                    response=data,
                    status=200,
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

    @endpoint('/scienti/info', methods=['GET'])
    def scienti_info(self):
        """
        @api {get} /scienti/info Scienti info endpoint
        @apiName Info
        @apiGroup Scienti
        @apiDescription information current Scienti database, such as users and tables for each database. 
                        This plugin have to be extecute inside the oracle container to do the local connection to
                        Oracle and to read the credention from the environmental variables, 
                        such as CVLAC_USER, GRUPLAC_USER, INSTITULAC_USER and ORACLE_PWD.
                        JSON was the format decided to return to avoid errors with csv due the separator.

        @apiParam {String} apikey  Credential for authentication
        @apiSuccess {Object}  Resgisters from OracleDB in Json format.

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        """
        if self.valid_apikey():
            data = {}
            data["CVLAC_USER"] = self.CVLAC_USER
            data["GRUPLAC_USER"] = self.GRUPLAC_USER
            data["INSTITULAC_USER"] = self.INSTITULAC_USER
            data["CVLAC_TABLES"] = self.cvlac_tables
            data["GRUPLAC_TABLES"] = self.grublac_tables
            data["INSTITULAC_TABLES"] = self.institulac_tables
            response = self.app.response_class(
                response=self.json.dumps(data),
                status=200,
                mimetype='application/json'
            )
            return response
        else:
            return self.apikey_error()

    @endpoint('/scienti/cvlac', methods=['GET'])
    def scienti_cvlac(self):
        """
        @api {get} /scienti/cvlac CVLaC data endpoint
        @apiName CVLaC
        @apiGroup Scienti
        @apiDescription information from queries made to CVLaC to OracleDB.

        @apiParam {String} apikey  Credential for authentication
        @apiParam {String} table  DB table required, if table="info" the list of tables available will be returned.
        @apiParam {String} orient  data orientation "split or records", default records (More common but more expensive in memory)
        @apiSuccess {Object}  Resgisters from OracleDB in Json format.

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        """
        table = self.request.args.get('table')
        orient = self.request.args.get('orient')
        if orient is None:
            orient = "records"
        if self.valid_apikey():
            if table in self.cvlac_tables:
                query = f"select distinct * from {self.CVLAC_USER}.{table}"
                df = pd.read_sql(query, con=self.oracle_db)
                data = df.to_json(orient=orient)
                response = self.app.response_class(
                    response=data,
                    status=200,
                    mimetype='application/json'
                )
                return response
            else:
                response = self.app.response_class(
                    response=self.json.dumps(
                        {"error": "Bad Request", "message": "table {table} not found on CVLAC, see available tables in tables_available", "tables_available": self.cvlac_tables}),
                    status=400,
                    mimetype='application/json'
                )
                return response
        else:
            return self.apikey_error()

    @endpoint('/scienti/gruplac', methods=['GET'])
    def scienti_gruplac(self):
        """
        @api {get} /scienti/gruplac GrupLaC data endpoint
        @apiName GrupLaC
        @apiGroup Scienti
        @apiDescription information from queries made to GrupLaC to OracleDB.

        @apiParam {String} apikey  Credential for authentication
        @apiParam {String} table  DB table required, if table="info" the list of tables available will be returned.
        @apiParam {String} orient  data orientation "split or records", default records (More common but more expensive in memory)
        @apiSuccess {Object}  Resgisters from OracleDB in Json format.

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        """
        table = self.request.args.get('table')
        orient = self.request.args.get('orient')
        if orient is None:
            orient = "records"
        if self.valid_apikey():
            if table in self.grublac_tables:
                query = f"select distinct * from {self.GRUPLAC_USER}.{table}"
                df = pd.read_sql(query, con=self.oracle_db)
                data = df.to_json(orient=orient)
                response = self.app.response_class(
                    response=data,
                    status=200,
                    mimetype='application/json'
                )
                return response
            else:
                response = self.app.response_class(
                    response=self.json.dumps(
                        {"error": "Bad Request", "message": "table {table} not found on GRUBLAC, see available tables in tables_available", "tables_available": self.grublac_tables}),
                    status=400,
                    mimetype='application/json'
                )
                return response
        else:
            return self.apikey_error()

    @endpoint('/scienti/institulac', methods=['GET'])
    def scienti_institulac(self):
        """
        @api {get} /scienti/institulac InstituLaC data endpoint
        @apiName Institulac
        @apiGroup Scienti
        @apiDescription information from queries made to InstituLaC to OracleDB

        @apiParam {String} apikey  Credential for authentication
        @apiParam {String} table  DB table required, if table="info" the list of tables available will be returned.
        @apiParam {String} orient  data orientation "split or records", default records (More common but more expensive in memory)
        @apiSuccess {Object}  Resgisters from OracleDB in Json format.

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        """
        table = self.request.args.get('table')
        orient = self.request.args.get('orient')
        if orient is None:
            orient = "records"
        if self.valid_apikey():
            if table in self.institulac_tables:
                query = f"select distinct * from {self.INSTITULAC_USER}.{table}"
                df = pd.read_sql(query, con=self.oracle_db)
                data = df.to_json(orient=orient)
                response = self.app.response_class(
                    response=data,
                    status=200,
                    mimetype='application/json'
                )
                return response
            else:
                response = self.app.response_class(
                    response=self.json.dumps(
                        {"error": "Bad Request", "message": "table {table} not found on INSTITULAC, see available tables in tables_available", "tables_available": self.grublac_tables}),
                    status=400,
                    mimetype='application/json'
                )
                return response
        else:
            return self.apikey_error()
