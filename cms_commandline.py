from cast.application import open_source_file, CASTAIP
import os.path
import uuid
import logging
import cast_upgrade_1_6_13 # @UnusedImport
from lxml import etree
import subprocess


def parse_settings(settings_file_path, major_minor):
    result = os.path.join(os.environ.get('APPDATA'), "CAST", "CAST", major_minor)            
    with open_source_file(settings_file_path) as fr:
        lines = fr.readlines()        
        for line in lines:            
            variable_index = line.find('CAST_CURRENT_USER_WORK_PATH') 
            if variable_index == -1:
                continue            
            semicolon_index = line.find(';')            
            commented = (semicolon_index > -1) and (semicolon_index < variable_index)            
            if not commented:
                result = line.split('=')[1].strip()   
                break    
    return os.path.normpath(result)


def ensure_cms_connection(application, connection_profile_path, engine, mb_name):
    from cast.application.internal.p1 import set_message # @UnresolvedImport    
    
    tree = etree.parse(connection_profile_path)
    root = tree.getroot()
    lot = next(iter(root))
    profiles1 = next(iter(lot))
    profiles2 = next(iter(profiles1))
    _type = 'connectionprofiles.ConnectionProfilePostgres'
    _p = 'CRYPTED2:' + set_message(engine.url.password)
    
    for connection in profiles2:
        try:
            if connection.tag == _type and connection.attrib['password'] == _p and \
               connection.attrib['user'] == engine.url.username and connection.attrib['schema'] == mb_name and \
               connection.attrib['host'] == engine.url.host and connection.attrib['port'] == str(engine.url.port):
                # already existing : nothing to do
                return connection.attrib['name']
        except KeyError:
            # it may happen sometimes that a line is incomplete
            # skip
            pass
        # add it
    _uuid = 'uuid:'+ str(uuid.uuid4())
    profiles2.append(etree.Element(_type, 
                                   {'entry':_uuid,
                                    'host':engine.url.host,
                                    'schema':mb_name,
                                    'port':str(engine.url.port),
                                    'user':engine.url.username,
                                    'name':application.name,
                                    'password':_p}))
    # write back
    tree.write(connection_profile_path, encoding='utf-8', xml_declaration=True)
    return application.name


def run_exec(args):
    try:
        subprocess.call(args, universal_newlines = True)
    except subprocess.CalledProcessError as e:
        logging.warning(e)
        logging.warning(e.output) 


def load_sources(appname,connection_profile):
    logging.info("Run Upload Sources...")
    command_line = [
        os.path.join(flat_path, "CAST-MS-CLI.exe"),
        "UploadSourcesInLocal",
        "-connectionProfile",
        connection_profile,
        "-appli",
        appname
   ]
    logging.info("Calling {}".format(command_line))
    run_exec(command_line)        
    logging.info("Run Upload Sources Done")


flat_path = CASTAIP.get_running_caip().get_path()
settings_file_path = os.path.join(flat_path, "CastGlobalSettings.ini")   
if not os.path.isfile(settings_file_path):
        logging.warning("The specified CAST installation folder does not contain any file named CastGlobalSettings.ini. Aborting")


aip = CASTAIP.get_running_caip()
split_version = str(aip.get_version()).split('.')       
connection_profiles_dir = parse_settings(settings_file_path, "{}.{}".format(split_version[0], split_version[1]))
if not os.path.isdir(connection_profiles_dir):
        logging.warning("The connection profiles folder specified in the settings does not exist ({})".format(connection_profiles_dir))

    
connection_profile_path = os.path.normpath(os.path.join(connection_profiles_dir, "cast-ms.connectionProfiles.pmx" ))        
if not os.path.isfile(connection_profile_path):
        logging.warning("The connection profiles folder specified in the settings does not contain a connection profile file ({})".format(connection_profile_path))
