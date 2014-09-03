import my_xml
import os
import subprocess

def parse_xml(xml):
    try:
        f = open(xml, 'r')
        pkl_xml = f.read()
        my_xml_obj = my_xml.parse(pkl_xml)
        f.close()
    except my_xml.MyXmlError:
        f.close()
        return None
    return my_xml_obj
    
def get_assets(xml_file):
    parsed = parse_xml(xml_file)
    return parsed.PackingList.AssetList.Asset
    
def get_xml_path(id, ASSETMAP):
    parsed = parse_xml(ASSETMAP)
    for x in parsed.AssetMap.AssetList.Asset:
        if x.Id == id:
            return x.ChunkList[0].Chunk.Path.value
    return False
    
def parse_cpl_subtitles(cpl, subtitle_list, ASSETMAP):
    parsed = parse_xml(cpl)
    for reel in parsed.CompositionPlaylist.ReelList.Reel:
        try:
            language = reel.AssetList.MainSubtitle.Language.value
        except:
            language = reel.AssetList.MainSubtitle.Id.value[-6:]
        subtitle_list.append({"subtitle_id": reel.AssetList.MainSubtitle.Id.value, "video_id": reel.AssetList.MainPicture.Id.value, 
                              "video_name": get_xml_path(reel.AssetList.MainPicture.Id.value, ASSETMAP), "language": language,
                              "subtitle_name":  get_xml_path(reel.AssetList.MainSubtitle.Id.value, ASSETMAP)})
    return subtitle_list

def build_subtitle_data(PKL, ASSETMAP):
    os.chdir(os.path.dirname(PKL))
    assets = get_assets(PKL)
    subtitle_data = []
    for asset in assets:
        if asset.Type == "text/xml;asdcpKind=CPL":
           subtitle_data = parse_cpl_subtitles(get_xml_path(asset.Id, ASSETMAP), subtitle_data, ASSETMAP)
    return subtitle_data
    
def convert_subtitles(subtitle_data, output_dir):
    for subtitle in subtitle_data:
        subprocess.check_call(r'"C:\Program Files\Subtitle Edit\SubtitleEdit.exe" /convert %s subrip /outputfolder:%s' % (subtitle['subtitle_name'], output_dir), shell=True)
        subrip_name = subtitle['video_name'].replace('.mxf', '') + '_' + subtitle['language'] + '.srt' 
        os.rename(os.path.join(output_dir, os.path.basename(subtitle['subtitle_name'].replace('.xml', '.srt'))), os.path.join(output_dir, subrip_name))
    
if __name__ == "__main__":
    subtitle_data = build_subtitle_data(r"C:\Users\bantonj\Downloads\la_boheme_test_subs\PKL__6d4367a1-a33b-4896-8d7b-76f02759a74b.xml", r"C:\Users\bantonj\Downloads\la_boheme_test_subs\ASSETMAP")
    convert_subtitles(subtitle_data, r"C:\subtest")