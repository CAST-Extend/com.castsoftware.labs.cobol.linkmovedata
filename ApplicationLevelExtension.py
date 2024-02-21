import cast_upgrade_1_6_13 # @UnusedImport
import logging
import SqlQueries as sqlq
from cast.application import ApplicationLevelExtension
import cms_commandline

class ApplicationLevelExtension(ApplicationLevelExtension):
    '''
    classdocs
    '''

    def end_application(self, application):
        logging.info('##################################################################')
        kb=application.get_knowledge_base()
        mb=application.get_managment_base()   
        mb_engine=mb.engine
        connection_profile=cms_commandline.ensure_cms_connection(application, cms_commandline.connection_profile_path, mb_engine, mb.name)

        logging.info('Update source code in KB...')
        logging.info('(1/2) Purging CODE_SourceRowOffsets...')
        kb.execute_query(sqlq.resetsourcerowoffsets())
        logging.info('(2/2) Loading sources...')
        cms_commandline.load_sources(application.name,connection_profile) 

        logging.info('Populating work tables...')
        kb.execute_query(sqlq.drop_temp_tables())
        logging.info('(1/3)')
        kb.execute_query(sqlq.populate_clrbook())
        logging.info('(2/3)')
        kb.execute_query(sqlq.populate_clebook())
        logging.info('(3/3)')
        kb.execute_query(sqlq.populate_bookmarks())
        kb.execute_query(sqlq.alter_bookmarks())
        kb.execute_query(sqlq.index_bookmarks())
        
        logging.info('Adding functions...')
        kb.execute_query(sqlq.create_cust_linkmovedata_code_extractbookmarktext())
        kb.execute_query(sqlq.create_cust_regexp_quote())

        logging.info('Retrieving bookmarks...')
        kb.execute_query(sqlq.retrieve_src_bookmarks())

        logging.info('Processing bookmarks...')
        logging.info('(0/12)')
        kb.execute_query(sqlq.discard_nomatch0_bookmarks())
        logging.info('(1/12)')
        kb.execute_query(sqlq.discard_nomatch1_bookmarks())
        logging.info('(2/12)')
        kb.execute_query(sqlq.discard_nomatch2_bookmarks())
        logging.info('(3/12)')
        kb.execute_query(sqlq.discard_nomatch3_bookmarks())
        logging.info('(4/12)')
        kb.execute_query(sqlq.discard_nomatch4_bookmarks())
        logging.info('(5/12)')
        kb.execute_query(sqlq.discard_nomatch5_bookmarks())
        logging.info('(6/12)')
        kb.execute_query(sqlq.discard_nomatch6_bookmarks())
        logging.info('(7/12)')
        kb.execute_query(sqlq.discard_nomatch7_bookmarks())
        logging.info('(8/12)')
        kb.execute_query(sqlq.discard_nomatch8_bookmarks())
        logging.info('(9/12)')
        kb.execute_query(sqlq.discard_nomatch9_bookmarks())
        logging.info('(10/12)')
        kb.execute_query(sqlq.discard_nomatch10_bookmarks())
        logging.info('(11/12)')
        kb.execute_query(sqlq.discard_nomatch11_bookmarks())
        logging.info('(12/12)')
        kb.execute_query(sqlq.discard_nomatch12_bookmarks())                

        logging.info('Creating links...')
        # Creates Aw link between source->target Cobol Data items in MOVE statements
        application.update_cast_knowledge_base("Create links between Cobol Data items", """        
        insert into CI_LINKS (CALLER_ID, CALLED_ID, LINK_TYPE, ERROR_ID)        
            select distinct idcle1, idcle2, 'accessWriteLink', 0
            from cust_bookmarks
        """)
        nblinks_rs=kb.execute_query(sqlq.get_sql_nblinks_created())
        for row in nblinks_rs:
            nblinks=row[0]
        logging.info('*********************************')
        logging.info('Number of links created: '+str(nblinks))
        logging.info('*********************************')
        logging.info('Removing work tables...')
        kb.execute_query(sqlq.drop_temp_tables())
        logging.info('##################################################################')
