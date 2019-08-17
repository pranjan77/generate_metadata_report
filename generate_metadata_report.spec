/*
A KBase module: generate_metadata_report
*/

module generate_metadata_report {

    typedef structure {
        string object_type;
        string workspace_name;
    } input;

    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_generate_metadata_report(input params) returns (ReportResults output) authentication required;

};
