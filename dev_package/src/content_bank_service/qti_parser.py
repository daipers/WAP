"""
qti_parser.py
=============

QTI (Question and Test Interoperability) import and export functionality.
Supports QTI 1.2 (XML) and QTI 3.0 (JSON) formats.

QTI is an IMS Global standard (1EdTech) for assessment content interchange.
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from pathlib import Path

from .models import AssessmentItem, ItemMetadata, ItemVersion


class QTIImporter:
    """
    Import assessment items from QTI packages.

    Supports:
    - QTI 1.2 (XML format)
    - QTI 3.0 (JSON format)
    """

    # QTI 1.2 namespace
    QTI_NS = {"qti": "http://www.imsglobal.org/xsd/ims_qtiasiv1p2"}

    def __init__(self):
        self.items: List[AssessmentItem] = []

    def import_from_file(self, path: str) -> List[AssessmentItem]:
        """
        Import items from a QTI file or package.

        Args:
            path: Path to QTI file (XML for QTI 1.2, JSON for QTI 3.0)

        Returns:
            List of AssessmentItem objects
        """
        path_obj = Path(path)

        if path_obj.suffix.lower() == ".json":
            return self._import_qti3(path)
        else:
            return self._import_qti12(path)

    def _import_qti12(self, path: str) -> List[AssessmentItem]:
        """Import QTI 1.2 XML format."""
        self.items = []

        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse QTI XML: {e}")

        # Find all item elements
        # QTI 1.2 uses <item> elements within <assessment>
        items_elem = root
        if root.tag.endswith("assessment") or "assessment" in root.tag:
            items_elem = root

        for item_elem in items_elem.findall(".//item"):
            item_data = self._parse_item(item_elem)
            if item_data:
                self._create_item_from_data(item_data)

        return self.items

    def _import_qti3(self, path: str) -> List[AssessmentItem]:
        """Import QTI 3.0 JSON format."""
        self.items = []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # QTI 3.0 JSON structure
        sections = data.get("assessmentSections", [])
        for section in sections:
            for item_data in section.get("items", []):
                item = self._parse_qti3_item(item_data)
                if item:
                    self.items.append(item)

        return self.items

    def parse_qti_manifest(self, manifest_path: str) -> dict:
        """
        Parse a QTI manifest file to extract item references.

        Args:
            manifest_path: Path to imsmanifest.xml

        Returns:
            Dict with resource references and metadata
        """
        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()
        except ET.ParseError:
            return {"resources": [], "metadata": {}}

        resources = []
        for res in root.findall(".//resource"):
            resources.append(
                {
                    "identifier": res.get("identifier", ""),
                    "type": res.get("type", ""),
                    "href": res.get("href", ""),
                }
            )

        return {"resources": resources, "metadata": {}}

    def _parse_item(self, item_elem) -> Optional[dict]:
        """
        Parse a QTI 1.2 item element into internal format.

        Args:
            item_elem: XML element representing the item

        Returns:
            Dict with parsed item data
        """
        identifier = item_elem.get("ident", item_elem.get("identifier", ""))
        if not identifier:
            return None

        # Extract presentation (prompt)
        presentation = item_elem.find(".//presentation")
        prompt = ""
        if presentation is not None:
            material = presentation.find(".//material")
            if material is not None:
                mattext = material.find("mattext")
                if mattext is not None:
                    prompt = mattext.text or ""

        # Extract response type
        response_type = "unknown"
        resprocessing = item_elem.find(".//resprocessing")
        if resprocessing is not None:
            # Check for correct response
            respcondition = resprocessing.find(".//respcondition")
            if respcondition is not None:
                response_type = "scored"

        # Extract response declarations (correct answers)
        correct_answer = None
        respdeclare = item_elem.find(".//respcondition/varequal")
        if respdeclare is not None:
            correct_answer = respdeclare.text

        return {
            "identifier": identifier,
            "prompt": prompt,
            "response_type": response_type,
            "gold_criteria": correct_answer,
            "allowed_tools": [],
            "constraints": {},
        }

    def _parse_qti3_item(self, item_data: dict) -> Optional[AssessmentItem]:
        """Parse a QTI 3.0 JSON item into AssessmentItem."""
        identifier = item_data.get("identifier", "")
        if not identifier:
            return None

        # Extract prompt
        prompt = ""
        if "prompt" in item_data:
            prompt = item_data["prompt"]
        elif "statement" in item_data:
            prompt = item_data["statement"]

        # Extract metadata
        metadata = ItemMetadata(
            tags=item_data.get("tags", []),
            difficulty=item_data.get("difficulty", 1),
            time_limit_minutes=item_data.get("timeLimit", 0),
            domain=item_data.get("domain", ""),
            skill_tags=item_data.get("skillTags", []),
        )

        # Create item
        item = AssessmentItem(
            item_id=identifier,
            current_version="1.0",
            metadata=metadata,
            versions=[],
            is_active=True,
        )

        # Add content as first version
        content = {
            "prompt": prompt,
            "response_type": item_data.get("responseType", "unknown"),
            "choices": item_data.get("choices", []),
            "correct_response": item_data.get("correctResponse", {}),
        }

        item.add_version(content, "qti-importer", "Imported from QTI 3.0")

        return item

    def _create_item_from_data(self, item_data: dict) -> AssessmentItem:
        """Create an AssessmentItem from parsed data."""
        # Create metadata
        metadata = ItemMetadata(
            tags=[], difficulty=1, time_limit_minutes=0, domain="", skill_tags=[]
        )

        # Create item
        item = AssessmentItem(
            item_id=item_data["identifier"],
            current_version="1.0",
            metadata=metadata,
            versions=[],
            is_active=True,
        )

        # Add content
        content = {
            "prompt": item_data.get("prompt", ""),
            "response_type": item_data.get("response_type", "unknown"),
            "gold_criteria": item_data.get("gold_criteria"),
            "allowed_tools": item_data.get("allowed_tools", []),
            "constraints": item_data.get("constraints", {}),
        }

        item.add_version(content, "qti-importer", "Imported from QTI 1.2")

        self.items.append(item)
        return item


class QTIExporter:
    """
    Export assessment items to QTI format.

    Currently supports QTI 1.2 XML output.
    """

    QTI_NS = "http://www.imsglobal.org/xsd/ims_qtiasiv1p2"

    def __init__(self):
        self.exported_items: List[str] = []

    def export_items(self, items: List[AssessmentItem], output_path: str) -> None:
        """
        Export items to QTI 1.2 XML format.

        Args:
            items: List of AssessmentItem objects to export
            output_path: Path to output XML file
        """
        root = ET.Element("questestinterop")

        for item in items:
            item_elem = self._item_to_qti_element(item)
            root.append(item_elem)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")

        with open(output_path, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)

        self.exported_items = [item.item_id for item in items]

    def item_to_qti(self, item: AssessmentItem) -> str:
        """
        Convert a single item to QTI XML string.

        Args:
            item: AssessmentItem to convert

        Returns:
            QTI 1.2 XML string
        """
        item_elem = self._item_to_qti_element(item)
        tree = ET.ElementTree(item_elem)

        import io

        output = io.BytesIO()
        tree.write(output, encoding="utf-8", xml_declaration=True)
        return output.getvalue().decode("utf-8")

    def _item_to_qti_element(self, item: AssessmentItem) -> ET.Element:
        """Convert AssessmentItem to QTI 1.2 XML element."""
        latest_content = item.get_latest_content()

        # Create item element
        item_elem = ET.Element("item")
        item_elem.set("ident", item.item_id)
        item_elem.set("title", item.item_id)

        # Add presentation section
        presentation = ET.SubElement(item_elem, "presentation")

        # Add material (prompt)
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext")
        mattext.set("texttype", "text/html")
        mattext.text = latest_content.get("prompt", "")

        # Add response declaration
        resproces = ET.SubElement(item_elem, "resprocessing")

        respident = ET.SubElement(resproces, "respident")
        respident.set("ident", "RESPONSE")

        # Handle multiple choice responses
        if latest_content.get("choices"):
            # Create render choice for multiple choice
            render_choice = ET.SubElement(presentation, "render_choice")

            for idx, choice in enumerate(latest_content["choices"]):
                response_label = ET.SubElement(render_choice, "response_label")
                response_label.set("ident", str(idx))

                material = ET.SubElement(response_label, "material")
                mattext = ET.SubElement(material, "mattext")
                mattext.text = choice

        # Add correct response if available
        if latest_content.get("gold_criteria"):
            respcondition = ET.SubElement(resproces, "respcondition")

            conditionvar = ET.SubElement(respcondition, "conditionvar")
            varequal = ET.SubElement(conditionvar, "varequal")
            varequal.set("respident", "RESPONSE")
            varequal.text = str(latest_content["gold_criteria"])

        # Add item metadata
        itemmetadata = ET.SubElement(item_elem, "itemmetadata")
        qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")

        # Add difficulty
        self._add_metadata_field(
            qtimetadata, "difficulty", str(item.metadata.difficulty)
        )

        # Add time limit
        if item.metadata.time_limit_minutes > 0:
            self._add_metadata_field(
                qtimetadata, "time_limit", str(item.metadata.time_limit_minutes)
            )

        return item_elem

    def _add_metadata_field(self, parent: ET.Element, label: str, value: str) -> None:
        """Add a metadata field to QTI metadata section."""
        field = ET.SubElement(parent, "qtimetadatafield")

        fieldlabel = ET.SubElement(field, "fieldlabel")
        fieldlabel.text = label

        fieldentry = ET.SubElement(field, "fieldentry")
        fieldentry.text = value
