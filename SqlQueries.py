def drop_temp_tables():
    return "drop table if exists clrbook, clebook, bookmarks"
def populate_clrbook():
    return """
    select acc.idclr, acc.idcle, acc.acctyplo, acc.acctyphi, accbook.* into temporary table clrbook
    from 
    acc,
    keys clr,
    keys cle,
    accbook
    where
        acc.acctyplo & 16777216=16777216
    and acc.acctyphi & 512=512 -- Ar
    and clr.objtyp in (606,548) -- COBOL Paragraph or Section
    and cle.objtyp in (831, 890, 114021, 142548) -- 'Cobol Data', 'Cobol Conditional Test', 'Cobol Literal', 'Cobol Index'
    and acc.idclr=clr.idkey
    and acc.idcle=cle.idkey    
    and accbook.idacc=acc.idacc
    """
def populate_clebook():
    return """
    select acc.idclr, acc.idcle, acc.acctyplo, acc.acctyphi, accbook.* into temporary table clebook
    from 
    acc,
    keys clr,
    keys cle,
    accbook
    where
        acc.acctyplo & 16777216=16777216
    and acc.acctyphi & 1024=1024 -- Aw
    and clr.objtyp in (606,548) -- COBOL Paragraph or Section
    and cle.objtyp in (831, 890, 142548) -- 'Cobol Data', 'Cobol Conditional Test', 'Cobol Index'
    and acc.idclr=clr.idkey
    and acc.idcle=cle.idkey    
    and accbook.idacc=acc.idacc
    """
def populate_bookmarks():
    return """
    select distinct clrbook.idclr,
                    clrbook.idacc as idacc1, clebook.idacc as idacc2, clrbook.idcle as idcle1, clebook.idcle as idcle2, 
                    clrbook.info1 as info11, clrbook.info2 as info21, clrbook.info3 as info31, clrbook.info4 as info41,
                    clebook.info1 as info12, clebook.info2 as info22, clebook.info3 as info32, clebook.info4 as info42,
                    clrbook.prop as prop1, clrbook.blkno as blkno1,
                    clebook.prop as prop2, clebook.blkno as blkno2,
                    clrbook.acctyphi as acctyphi1, clebook.acctyphi as acctyphi2,
                    k1.keynam as keynam1,
                    k2.keynam as keynam2,
                    k1.objtyp as objtyp1,
                    k2.objtyp as objtyp2
    into temporary table bookmarks
    from 
        clrbook,clebook,keys k1,keys k2
    where
        clrbook.idclr=clebook.idclr
    and clrbook.idcle=k1.idkey
    and clebook.idcle=k2.idkey
    and clrbook.info1=clebook.info1
    and clrbook.info2=clebook.info2
    and clrbook.info3=clebook.info3
    and clrbook.info4=clebook.info4
    and clrbook.idcle!=clebook.idcle
    order by 1
    """

def index_bookmarks():
    return "CREATE INDEX bmcode1_idx ON bookmarks (bmcode1)"

def alter_bookmarks():
    return "alter table bookmarks add column bmcode1 text, add column bmcode2 text"

def retrieve_src_bookmarks():
    # Retrieve bookmark src for statements
    return """
    update bookmarks set bmcode1 = ltrim(cust_linkmovedata_extension_code_extractbookmarktext(idacc1,info11,info21,info31,info41,prop1,blkno1)),
                         bmcode2 = ltrim(cust_linkmovedata_extension_code_extractbookmarktext(idacc2,info12,info22,info32,info42,prop2,blkno2))
    """

def discard_nomatch0_bookmarks():
    return """
    delete from bookmarks where 
                         bmcode1 is null or bmcode2 is null
    """
    
def discard_nomatch1_bookmarks():
    return """
    delete from bookmarks where 
                         bmcode1 != bmcode2 -- Bookmark mismatch
    """

def discard_nomatch2_bookmarks():
    return r"""
    delete from bookmarks where 
                     not bmcode1 ~* '^ADD\s' 
                 and not bmcode1 ~* '^SUBTRACT\s' 
                 and not bmcode1 ~* '^MULTIPLY\s' 
                 and not bmcode1 ~* '^DIVIDE\s' 
                 and not bmcode1 ~* '^COMPUTE\s' 
                 and not bmcode1 ~* '^SET\s' 
                 and not bmcode1 ~* '^STRING\s'
                 and not bmcode1 ~* '^UNSTRING\s'
                 and not bmcode1 ~* '^MOVE\s' 
    """

def discard_nomatch3_bookmarks():
    return r"""
    delete from bookmarks where 
                         bmcode1 ~*  '^MOVE\s'
                 and (
                     not bmcode1 ~* ('TO\s+[A-Z0-9\-\,\:\(\)\s]*'||cust_regexp_quote(keynam2))    -- Does not match "MOVE ... TO keynam2 ..." => discard 
                     or  bmcode1 ~* ('TO\s+[A-Z0-9\-\,\:\(\)\s]*'||cust_regexp_quote(keynam1)||'(\s|\,|\(|$)')    -- Matches "MOVE ... TO keynam1" => discard 
                     )                        
    """ 

def discard_nomatch4_bookmarks():
    return r"""
    delete from bookmarks where  
                       not bmcode1 ~* ('(^ADD|^ADD\s+CORR|^ADD\s+CORRESPONDING|^SUBTRACT|^SUBTRACT\s+CORR|^SUBTRACT\s+CORRESPONDING|^MULTIPLY|^DIVIDE|^COMPUTE|^SET|^MOVE|^MOVE\s+CORR|^MOVE\s+CORRESPONDING)\s+'||cust_regexp_quote(keynam1)||'[\s\,\=\(]')
                  and  not bmcode1 ~* ('FUNCTION\s+[A-Z\-]+\s+\(\s*'||cust_regexp_quote(keynam1)||'\s*\)')
                  and (
                       bmcode1 ~* ('[A-Z0-9]+\s*\(\s*'||cust_regexp_quote(keynam1)||'\s*\)')       or           -- matches "AA-BB (COBOL-INDEX)" 
                       bmcode1 ~* ('[A-Z0-9]+\s*\(\s*'||cust_regexp_quote(keynam1)||'[\s\,]')      or           -- matches "AA-BB (COBOL-INDEX ,... " 
                       bmcode1 ~* ('[A-Z0-9]+\s*\([\sA-Z0-9\-\+\*\,]+'||cust_regexp_quote(keynam1)||'[\s\,\)]') -- matches "AA-BB ( ..., COBOL-INDEX)"  or "AA-BB ( ..., COBOL-INDEX , "
                       )
    """

def discard_nomatch5_bookmarks():
    return r"""
    delete from bookmarks where 
                       not bmcode1 ~* ('(^ADD|^ADD\s+CORR|^ADD\s+CORRESPONDING|^SUBTRACT|^SUBTRACT\s+CORR|^SUBTRACT\s+CORRESPONDING|^MULTIPLY|^DIVIDE|^COMPUTE|^SET|^MOVE|^MOVE\s+CORR|^MOVE\s+CORRESPONDING)\s+'||cust_regexp_quote(keynam2)||'[\s\,\=\(]')
                  and  not bmcode1 ~* ('FUNCTION\s+[A-Z\-]+\s+\(\s*'||cust_regexp_quote(keynam2)||'\s*\)')
                  and (
                       bmcode1 ~* ('[A-Z0-9]+\s*\(\s*'||cust_regexp_quote(keynam2)||'\s*\)')       or           -- matches "AA-BB (COBOL-INDEX)" 
                       bmcode1 ~* ('[A-Z0-9]+\s*\(\s*'||cust_regexp_quote(keynam2)||'[\s\,]')      or           -- matches "AA-BB (COBOL-INDEX ,... " 
                       bmcode1 ~* ('[A-Z0-9]+\s*\([\sA-Z0-9\-\+\*\,]+'||cust_regexp_quote(keynam2)||'[\s\,\)]') -- matches "AA-BB ( ..., COBOL-INDEX)"  or "AA-BB ( ..., COBOL-INDEX , "
                       )
    """

def discard_nomatch6_bookmarks():
    return r"""
    delete from bookmarks where                          
                         bmcode1 ~*  '^STRING\s'
                 and ( 
                         not bmcode1 ~* ('INTO\s+'||cust_regexp_quote(keynam2)) -- Does not match "STRING ... INTO keynam2 ..." => discard
                         or  bmcode1 ~* ('INTO\s+'||cust_regexp_quote(keynam1)||'[\s\(\,]') -- Matches "STRING ... INTO keynam1 ..." => discard
                         or  bmcode1 ~* ('DELIMITED\s+BY\s+'||cust_regexp_quote(REGEXP_REPLACE(keynam1, '\"', '''', 'g'))||'[\s\(\,]') 
                     )
    """

def discard_nomatch7_bookmarks():
    return r"""
    delete from bookmarks where 
                             bmcode1 ~*  '^UNSTRING\s'
                 and (
                         not bmcode1 ~* ('UNSTRING\s+'||cust_regexp_quote(keynam1)||'[\s\(]+') -- Does not match "UNSTRING keynam1 ..." => discard
                         or  bmcode1 ~* ('UNSTRING\s+'||cust_regexp_quote(keynam2)||'[\s\(]+') -- Matches "UNSTRING keynam2 ..." => discard
                     )
    """

def discard_nomatch8_bookmarks():
    return r"""
    delete from bookmarks where                          
                         bmcode1 ~*  '^COMPUTE\s' 
                 and (
                    not  bmcode1 ~* ('COMPUTE\s+'||cust_regexp_quote(keynam2)||'[\s\(\=]') -- Does not match "COMPUTE keynam2 ..." => discard
                    or   bmcode1 ~* ('COMPUTE\s+'||cust_regexp_quote(keynam1)||'[\s\(\=]') -- Matches "COMPUTE keynam1 ..." => discard
                     )
    """

def discard_nomatch9_bookmarks():
    return r"""
    delete from bookmarks where                                                   
                           bmcode1 ~*  '^SET\s' 
                 and (
                        not bmcode1 ~* ('SET\s+'||cust_regexp_quote(keynam2)||'[\s\(]') -- Does not match "SET keynam2 ..." => discard
                     or     bmcode1 ~* ('SET\s+'||cust_regexp_quote(keynam1)||'[\s\(]') -- Matches "SET keynam1 ..." => discard
                     or     bmcode1 ~* ('TO\s+'||cust_regexp_quote(keynam2)||'[\s\(]') 
                     )
    """

def discard_nomatch10_bookmarks():
    return r"""
    delete from bookmarks where 
                 -- ADD, SUBTRACT, MULTIPLY, DIVIDE instructions:
                         bmcode1 ~* '(^ADD|^SUBTRACT|^MULTIPLY|^DIVIDE)\s' 
                 and not bmcode1 ~* 'GIVING\s'
                 and (
                     not bmcode1 ~* ('(FROM|TO|BY|INTO)\s'||'[A-Z0-9\-\+\,\(\)\s]*'||cust_regexp_quote(keynam2)||'(\s|\,|\(|$)')
                  or     bmcode1 ~* ('(FROM|TO|BY|INTO)\s'||'[A-Z0-9\-\+\,\(\)\s]*'||cust_regexp_quote(keynam1)||'(\s|\,|\(|$)')
                     )
    """ 

def discard_nomatch11_bookmarks():
    return r"""
    delete from bookmarks where 
                 -- ADD, SUBTRACT, MULTIPLY, DIVIDE instructions with GIVING:
                            bmcode1 ~* '(^ADD|^SUBTRACT|^MULTIPLY|^DIVIDE)\s' 
                 and     (                 
                            bmcode1 ~* ('\s+(GIVING)\s+'||cust_regexp_quote(keynam1)||'(\s|\(|$)' )
                     or     bmcode1 ~* ('\s+(REMAINDER)\s+'||cust_regexp_quote(keynam1)||'(\s|\(|$)' )
                         )
    """   

def discard_nomatch12_bookmarks():
    return r"""
    delete from bookmarks where 
                 -- ADD, SUBTRACT, MULTIPLY, DIVIDE instructions with GIVING:
                       bmcode1 ~* '(^ADD|^SUBTRACT|^MULTIPLY|^DIVIDE)\s' 
                 and   bmcode1 ~* ('[\s\,]+'||cust_regexp_quote(keynam2)||'[\s\(\,].*'||'GIVING\s')  -- No target left of GIVING
    """       

def get_sql_nblinks_created():    
    return "select count(distinct (idcle1, idcle2)) from bookmarks"

def create_cust_linkmovedata_code_extractbookmarktext():
    # Function to retrieve bookmark src
    return r"""
    CREATE OR REPLACE FUNCTION cust_linkmovedata_extension_code_extractbookmarktext(
        i_idacc integer,
        i_info1 integer,
        i_info2 integer,
        i_info3 integer,
        i_info4 integer,
        i_prop integer,
        i_blkno integer)
        RETURNS text
        LANGUAGE 'plpgsql'
    AS $BODY$
    declare
        L_sourceId int;
        L_source text;
        L_mainStartRow int;
        L_mainStartColumn int;
        L_mainEndRow int;
        L_mainEndColumn int;
        L_startRow int;
        L_startColumn int;
        L_endRow int;
        L_endColumn int;
    begin
        select dcs.SOURCE_ID as sourceId,
                        dcs.SOURCE_CODE as source,
                        op.Info1 as mainStartRow,
                        op.Info2 as mainStartColumn,
                        op.Info3 as mainEndRow,
                        op.Info4 as mainEndColumn,
                        ab.Info1 as startRow,
                        ab.Info2 as startColumn,
                        ab.Info3 as endRow,
                        ab.Info4 as endColumn
                   into L_sourceId,    
                        L_source,
                        L_mainStartRow,
                        L_mainStartColumn,
                        L_mainEndRow,
                        L_mainEndColumn,
                        L_startRow,
                        L_startColumn,
                        L_endRow,
                        L_endColumn
                   from AccBook ab
                   join Acc a
                     on a.IdAcc = ab.IdAcc
                   join ObjPos op
                     on op.IdObj = a.IdClr
                    and (op.BlkNo = 0 or op.BlkNo = ab.BlkNo)
                   join ObjFilRef ofr
                     on (ofr.IdObj = op.IdObj or ofr.IdObj = op.IdObjRef)
                    and (ofr.IdFil = 0 or ofr.IdFil = op.IdObjRef)
                   join RefPath rp
                     on rp.IdFilRef = ofr.IdFilRef
                   join DSS_CODE_SOURCES dcs
                     on dcs.SOURCE_PATH = rp.Path
                  where ab.IdAcc = I_IdAcc
                    and ab.info1=i_info1 and ab.info2=i_info2 and ab.info3=i_info3 and ab.info4=i_info4 
                    and ab.prop=i_prop and ab.blkno=i_blkno;
    
        if L_source is  null
        then
            return null;
        end if;
    
        return CODE_extractBookmarkText(L_sourceId, L_source, L_mainStartRow, L_mainStartColumn, L_mainEndRow, L_mainEndColumn, L_startRow, L_startColumn, L_endRow, L_endColumn);
    
    end;
    $BODY$;
    """

def create_cust_regexp_quote():
    # Function to escape all regexp special characters in a string
    return r"""    
    CREATE OR REPLACE FUNCTION cust_regexp_quote(IN TEXT)
        RETURNS TEXT
        LANGUAGE plpgsql
        STABLE
    AS $BODY$
        /*******************************************************************************
        * Function Name: regexp_quote
        * In-coming Param:
        *   The string to decoded and convert into a set of text arrays.
        * Returns:
        *   This function produces a TEXT that can be used as a regular expression
        *   pattern that would match the input as if it were a literal pattern.
        * Description:
        *   Takes in a TEXT in and escapes all of the necessary characters so that
        *   the output can be used as a regular expression to match the input as if
        *   it were a literal pattern.
        * Source: https://cwestblog.com/2012/07/10/postgresql-escape-regular-expressions/ * 
        *     The original one doesn't work anymore. ???
        ******************************************************************************/
    BEGIN
        RETURN REGEXP_REPLACE($1, '([\-\.\+\*\?\^\$\(\)\[\]\{\}\|\\])', '\\\1', 'g');
    END;
    $BODY$;
    """
