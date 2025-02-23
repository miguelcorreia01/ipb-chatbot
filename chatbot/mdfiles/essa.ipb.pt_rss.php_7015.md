Source: http://essa.ipb.pt/rss.php

getQuery(true); $query->select('m.params'); $query->from('#__modules AS m');
$query->where($db->quoteName('module') . ' = '.
$db->quote('mod_atualidades')); $db->setQuery($query); $module =
$db->loadObject(); $moduleParams = new JRegistry($module->params); $option =
array(); $option['driver']='mysqli';
$option['host']=$moduleParams->get('host');
$option['user']=$moduleParams->get('user');
$option['password']=$moduleParams->get('password');
$option['database']=$moduleParams->get('database');
$option['table']=$moduleParams->get('table');
$pagina=$moduleParams->get("pagina"); $db = JDatabase::getInstance( $option );
@$categoria=$_GET['categoria']; $sql = "SELECT
id,DATE_FORMAT(data_publicacao,'%d/%m/%Y') as
data_pub,titulo,resumo,apresentacao,rss FROM actualidade ";
if($categoria==NULL)$sql .= "where apagado=0 and visivel=1 and listagem=1 and
instituicao like '%ESSA,%' "; else $sql .= "where apagado=0 and visivel=1 and
instituicao like '%ESSA,%' and categorias like '%$categoria%' "; $sql .=
"ORDER BY posicao,data_publicacao DESC"; $db->setQuery($sql); $db->query();
$results = $db->loadObjectList(); $xml = '' . "\n"; print("$xmlAtualidades da
ESSAhttp://www.essa.ipb.ptpt-pthttp://essa.ipb.pt/templates/essa-template-
geral/images/logo.pngAtualidades da ESSahttp://www.essa.ipb.pt35450");
function clear_text_js($s) {$do = true; while ($do) {$start = stripos($s,'<
script'); $stop = stripos($s,'> < /script> '); if
((is_numeric($start))&&(is_numeric($stop))) {$s =
substr($s,0,$start).substr($s,($stop+strlen('> < /script> '))); } else {$do =
false; }}return trim($s); }function clear_text_div($s) {$do = true; while
($do) {$start = stripos($s,'< div'); $stop = stripos($s,'< /div> '); if
((is_numeric($start))&&(is_numeric($stop))) {$s =
substr($s,0,$start).substr($s,($stop+strlen('< /div> '))); } else {$do =
false; }}return trim($s); }function decode_entities($text) {$text=
html_entity_decode($text,ENT_QUOTES,"ISO-8859-1"); $text=
preg_replace('/&#(\d+); /me',"chr(\\\1)",$text); $text=
preg_replace('/&#x([a-f0-9]+); /mei',"chr(0x\\\1)",$text); return $text;
}$i=0; foreach ($results as $row) : $tit=html_entity_decode($row->titulo);
$res=html_entity_decode($row->resumo); $res=str_replace('&','& ',$res);
$des=clear_text_js($row->apresentacao); $des=clear_text_div($des);
$des=htmlentities(decode_entities($row->apresentacao)); $i++; if($i<30)echo
''.$tit.''.$pagina.'?pub='.$row->id.''.$pagina.'?pub='.$row->id.''.$row->rss.'
+0100'.$res.' '.$des.''; endforeach; print(""); ?>

  *[ 23 Outubro ]: 2024-10-23
  *[ 25 Outubro ]: 2024-10-25