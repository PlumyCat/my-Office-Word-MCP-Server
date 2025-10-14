Là j'ai pu connecté les tools avec cette méthode mais c super chiant il faut mettre une par une. j'ai pu en mettre 48. il y a un souci sur cette liste car il y a pas d'entrée elle sont donc pas utiliseable :

"
List all .docx files in the specified directory.

Get the raw XML structure of a Word document.

Get detailed information about a specific template.

Insert a numbered list before or after the target paragraph.

Get the structure of a Word document.

Get text from a specific paragraph in a Word document.

Check if a document exists in storage with detailed diagnostics.

Search for text and replace all occurrences.

Get information about a Word document.

Extract all text from a Word document.

Extract all comments from a Word document.

Extract comments from a specific author in a Word document.

List all ContentControls (structured fields) in the document.

Find occurrences of specific text in a Word document.

Extract comments for a specific paragraph in a Word document."

Pour cette liste il y a un souci d'entrée on demande un path qui est pas cohérent avec le system je pense que c un reliquat du projet d'origine qui était un srrveur MCP local et le dernier est en espagnol là je vois pas pourquoi : 
"
Replace all content between start_anchor_text and end_anchor_tex > Doc Path

Insert a header (with specified style) before or after the targe > Doc Path

Insert a new line or paragraph (with specified or matched style) > Doc Path

Reemplaza el bloque de párrafos debajo de un encabezado, evitando modificar TOC. > Doc Path"


En plus il y a un souci général par ex avec "List ALL available templates." j'ai l'erreur : "Message d’erreur : L’évaluation de l’expression PowerFx a entraîné une erreur lors de l’appel du connecteur : PVA.ListAllTemplates failed: PowerFxJsonException Expecting String but received a Record Code d’erreur : ConnectorPowerFxError ID de conversation : 62dd681f-8e30-460c-9989-3c112bf65df3 Heure (UTC) : 2025-10-10T09:47:21.939Z" 

"connectorPowerFxErrorL’évaluation de l’expression PowerFx a entraîné une erreur lors de l’appel du connecteur : PVA.ListAllTemplates failed: PowerFxJsonException Expecting String but received a Record"

Si je me trompe pas là c parceque la sortie est déclaré sur le swagger comme string alors qu'il reçoit un json ex : 

"{
  "result": "Found 7 Word documents in storage:\n- mon_document_client.docx (2030.01 KB) (EXPIRED)\n  Created: 2025-10-08T10:10:59.887948\n  Expires: 2025-10-09T10:10:59.887934\n  URL: https://mywordmcpacrstorage.blob.core.windows.net/word-documents/mon_document_client.docx?se=2025-10-11T10%3A03%3A23Z&sp=r&sv=2025-07-05&sr=b&sig=HYfhUf/o5ghEv66jmJOs4XA9WKBrTHiutuVjRW%2Bds8c%3D\n- propal_template_text.docx (2024.11 KB) (EXPIRED)\n  Created: 2025-10-09T08:06:09.764885\n  Expires: 2025-10-10T08:06:09.764875\n  URL: https://mywordmcpacrstorage.blob.core.windows.net/word-documents/propal_template_text.docx?se=2025-10-11T10%3A03%3A23Z&sp=r&sv=2025-07-05&sr=b&sig=59vRt9QcI94eOY99acjRm4GGigvI20u4Zctdaf%2B5i4g%3D\n- proposal_john_do.docx (2024.09 KB) (EXPIRED)\n  Created: 2025-10-09T08:34:43.673776\n  Expires: 2025-10-10T08:34:43.673762\n  URL: https://mywordmcpacrstorage.blob.core.windows.net/word-documents/proposal_john_do.docx?se=2025-10-11T10%3A03%3A23Z&sp=r&sv=2025-07-05&sr=b&sig=AFVpxMxp78J%2BZwHps0%2Bx1yjJvjrsQfcAfeVnOJys5AM%3D\n- proposal_john_do_template-text.docx (2023.68 KB) (EXPIRED)\n  Created: 2025-10-09T08:27:15.093098\n  Expires: 2025-10-10T08:27:15.093084\n  URL: https://mywordmcpacrstorage.blob.core.windows.net/word-documents/proposal_john_do_template-text.docx?se=2025-10-11T10%3A03%3A23Z&sp=r&sv=2025-07-05&sr=b&sig=ACmnTn2K960s/a62JFONxWQboWcxgvU4GFkY%2B53GGkY%3D\n- sample_template.docx (35.72 KB) (EXPIRED)\n  Created: 2025-10-08T10:05:08.270822\n  Expires: 2025-10-09T10:05:08.270811\n  URL: https://mywordmcpacrstorage.blob.core.windows.net/word-documents/sample_template.docx?se=2025-10-11T10%3A03%3A23Z&sp=r&sv=2025-07-05&sr=b&sig=3dJreFmifvlM80GQnQ4gqxdTpyJrqW0LfPiE23VRMs4%3D\n- test_ctrl.docx (2029.69 KB) (EXPIRED)\n  Created: 2025-10-08T10:35:13.273025\n  Expires: 2025-10-09T10:35:13.273010\n  URL: https://mywordmcpacrstorage.blob.core.windows.net/word-documents/test_ctrl.docx?se=2025-10-11T10%3A03%3A23Z&sp=r&sv=2025-07-05&sr=b&sig=4KVjcvS35R4zedY35ttlqHf4CIVhIeyqtwgpun4XBK8%3D\n- test_replace_text.docx (2023.68 KB) (EXPIRED)\n  Created: 2025-10-08T13:35:21.031757\n  Expires: 2025-10-09T13:35:21.031747\n  URL: https://mywordmcpacrstorage.blob.core.windows.net/word-documents/test_replace_text.docx?se=2025-10-11T10%3A03%3A23Z&sp=r&sv=2025-07-05&sr=b&sig=9pXVuV8LyAFUhe6Pn0OsgR%2B2KyETFrcJJ32WWk20AO8%3D\n"
}"


et aussi la réponse sont assez longue sachant que MS a rien  trouvé de mieux que de mettre untimeout de 30 sec, là on est très juste je vois pas pourquoi on avait pas ce souci jusqu'ici 