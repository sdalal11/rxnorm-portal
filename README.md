# RxNorm Document Portal

A web-based medical document annotation platform for healthcare professionals.

## 🌐 Live Demo
Visit: [https://yourusername.github.io/rxnorm-portal](https://yourusername.github.io/rxnorm-portal)

## ✨ Features
- **Document Management**: Upload and organize medical documents
- **AI-Powered Annotations**: Automatic medication detection with RxNorm codes
- **User Authentication**: Secure login for healthcare professionals
- **Collaborative Annotations**: Mark medications as active/inactive
- **Azure Integration**: Cloud storage for documents and annotations

## 🚀 Quick Start

### For Users:
1. Visit the [User Portal](user.html)
2. Register or login with demo account:
   - Email: `demo@doctor.com`
   - Password: `demo123`
3. Browse and annotate documents

### For Administrators:
1. Visit the [Admin Interface](admin.html)
2. Configure Azure storage settings
3. Upload and manage documents

### Demo Setup:
1. Visit [Setup Page](setup.html)
2. Click "Setup Demo Data" for instant testing
3. Access both admin and user interfaces

## 🏥 Use Cases
- **Medication Reconciliation**: Review and validate patient medications
- **Clinical Documentation**: Annotate discharge summaries and medical records
- **Pharmacy Reviews**: Track active vs discontinued medications
- **Research**: Analyze medication patterns with RxNorm standardization

## 🔧 Technical Stack
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Storage**: Azure Blob Storage + localStorage
- **Authentication**: Client-side with secure session management
- **AI Processing**: Python backend with RxNorm API integration

## 📁 Files Structure
```
├── user.html          # Main user interface
├── admin.html         # Administrator dashboard  
├── setup.html         # Demo data configuration
├── main.py            # Backend processing (Python)
└── README.md          # Documentation
```

## 🏗️ Deployment
This portal is deployed using GitHub Pages and can be easily forked and customized for different healthcare organizations.

## 📊 Demo Data
The setup includes sample medical documents with:
- Patient medication lists
- Discharge summaries
- Medication review reports
- Pre-annotated medications with RxNorm codes

## 🔐 Security Notes
- For production use, implement proper authentication
- Use HTTPS for all communications
- Secure Azure storage with appropriate access controls
- Hash passwords on server side

## 📝 License
MIT License - Feel free to use and modify for your healthcare organization.

---
Built for healthcare professionals to improve medication management and clinical documentation.