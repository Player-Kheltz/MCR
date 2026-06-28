import xml.etree.ElementTree as ET

def correct_items_xml(file_path):
    """
    Corrige o arquivo items.xml, removendo tags vazias e corrigindo a formatação.
    
    :param file_path: Caminho para o arquivo items.xml
    """
    # Carrega o XML do arquivo
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Função recursiva para remover tags vazias
    def remove_empty_tags(element):
        for child in element:
            if not child.text.strip() and len(child) == 0:
                element.remove(child)
            else:
                remove_empty_tags(child)
    
    # Remove tags vazias do arquivo
    remove_empty_tags(root)
    
    # Corrige a formatação do XML
    tree.write(file_path, encoding='utf-8', xml_declaration=True)

# Exemplo de uso
file_path = 'WL/Costura_de_tecido_para_iniciantes_0001/items.xml'
correct_items_xml(file_path)