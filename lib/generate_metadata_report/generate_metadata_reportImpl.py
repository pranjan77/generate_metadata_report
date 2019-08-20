# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import pandas as pd
import uuid
from installed_clients.WorkspaceClient import Workspace
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.DataFileUtilClient import DataFileUtil

#END_HEADER


class generate_metadata_report:
    '''
    Module Name:
    generate_metadata_report

    Module Description:
    A KBase module: generate_metadata_report
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    def _mkdir_p(self, path):
        """
        _mkdir_p: make directory for given path
        """
        if not path:
            return
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def write_pd_html(self, df, path):
        html_string = '''
        <html>
        <head><title>Report</title></head>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.19/css/jquery.dataTables.min.css"/>
        <script type="text/javascript" language="javascript" src="https://code.jquery.com/jquery-3.3.1.js"></script>
        <script type="text/javascript" language="javascript" src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
        <script type="text/javascript" class="init">
        $(document).ready(function() {
            $('#example').DataTable();
            } );
        </script>
        <body>
        '''
        uid = str(uuid.uuid4())
        uidx= "#" + uid
        html_string =html_string.replace('#example', uidx )
        table = df.to_html(table_id=uid)
        html_string += table
        html_string += '''
        </body>
        </html>
        '''
        with open(path , 'w') as f:
            f.write(html_string)



    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        self.ws_url = config['workspace-url']
        self.dfu = DataFileUtil(self.callback_url)
        #END_CONSTRUCTOR
        pass



    def run_generate_metadata_report(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_generate_metadata_report
        object_type = params['object_type']
        workspace_name = params['workspace_name']

        ws = Workspace(self.ws_url)
        print (params)



        objects_in_workspace = ws.list_objects({'workspaces': [workspace_name],'type': object_type})
        object_names = sorted ([j[1] for j in objects_in_workspace])

        d = dict()

        if (object_type == 'KBaseRNASeq.RNASeqAlignment'):
            for object_name in object_names:
                alignment_stats = ws.get_objects2({'objects': [{'workspace': workspace_name, 'name': object_name}]})['data'][0]['data']['alignment_stats']
                metadata_keys = alignment_stats.keys()
                object_pd = pd.Series(alignment_stats,index = metadata_keys)
                d[object_name] = object_pd 

        else:
            for object_name in object_names:
                obj_meta_data = ws.get_object_info3({'objects': [{'workspace': workspace_name, 'name': object_name}], 'includeMetadata':1}, )
                metadata = obj_meta_data.get('infos')[0][10]
                metadata_keys = metadata.keys()
                object_pd = pd.Series(metadata,index = metadata_keys)
                d[object_name] = object_pd 



        df = pd.DataFrame(d)

        


        htmlDir = os.path.join(self.shared_folder, str(uuid.uuid4()))
        self._mkdir_p(htmlDir)
        report_file_path = os.path.join(htmlDir, "index.html")
        #df.to_html(report_file_path)
        self.write_pd_html(df.T, report_file_path)

        try:
            html_upload_ret = self.dfu.file_to_shock({'file_path': htmlDir, 'make_handle': 0, 'pack': 'zip'})
        except Exception:
            raise ValueError('Error uploading HTML file: ' + str(htmlDir) + ' to shock')

        reportname = 'generate_metadata_report_' + str(uuid.uuid4())

        reportobj = {
            'message': '',
            'direct_html': None,
            'direct_html_link_index': 0,
            'file_links': [],
            'html_links': [],
            'html_window_height': 500,
            'workspace_name': params['workspace_name'],
            'report_object_name': reportname
        }

        # attach to report obj
        reportobj['direct_html'] = ''
        reportobj['direct_html_link_index'] = 0
        reportobj['html_links'] = [{'shock_id': html_upload_ret['shock_id'],
                                    'name': 'index.html',
                                    'label': 'index.html'}]

        report = KBaseReport(self.callback_url, token=ctx['token'])
        report_info = report.create_extended_report(reportobj)
        output = {'report_name': report_info['name'], 'report_ref': report_info['ref']}


        print (output)



        #END run_generate_metadata_report

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_generate_metadata_report return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
