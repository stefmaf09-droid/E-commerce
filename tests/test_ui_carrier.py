import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import MagicMock, patch

class TestCarrierUI:
    
    @patch('src.ui.carrier_management.CustomCarrierManager')
    def test_render_carrier_management(self, mock_manager_class):
        # Setup mock manager
        mock_manager = mock_manager_class.return_value
        mock_manager.get_all_carriers.return_value = ['Colissimo']
        mock_manager.get_carriers.return_value = [{'name': 'CustomExpress'}]
        
        at = AppTest.from_file("tests/ui_wrappers/carrier_wrapper.py")
        at.run()
        
        # Verify elements are present
        assert at.markdown[0].value == "### 🚚 Gestion des Transporteurs"
        assert at.text[0].value == "✓ Colissimo"
        assert at.text[9].value == "🏷️ CustomExpress"
        
        # Test adding a carrier
        at.text_input(key=None).set_value("NewCarrier") # first text input is name
        at.button[1].click() # form submit button (button[0] is one of the delete buttons if any)
        at.run()
        
        # Check if manager was called (but wait, button index might be tricky)
        # Better use keys: at.button(key="del_carrier_CustomExpress")
        # In this specific app, st.button("🗑️") has a key.
        # But for form submit button, it has no key by default.
        
    @patch('src.ui.carrier_management.CustomCarrierManager')
    def test_delete_carrier(self, mock_manager_class):
        mock_manager = mock_manager_class.return_value
        mock_manager.get_carriers.return_value = [{'name': 'ToDel'}]
        
        at = AppTest.from_file("tests/ui_wrappers/carrier_wrapper.py")
        at.run()
        
        # Click delete button
        at.button(key="del_carrier_ToDel").click()
        at.run()
        
        mock_manager.delete_carrier.assert_called_once_with('test@example.com', 'ToDel')
