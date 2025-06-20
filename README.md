# Setup Instructions for the Lost Children Facial Recognition System

## Project Overview

This project aims to support the recovery of lost or unidentified children and help reunite them with their families using facial recognition technology.  
The core idea is to analyze a child’s facial image and compare it against a database of previously recorded faces. If a match is found:

- The system retrieves the child's stored information.
- The family is contacted using the available contact details.
- Authorities are notified to safely return the child to their family.

---

## Prerequisites

To run the project successfully, make sure the following tools are installed in your environment:

- Visual Studio 2022 or later, with:
  - ASP.NET Core support  
  - Entity Framework Core  
  - NuGet Package Manager

- Microsoft SQL Server  
  It is recommended to use SQL Server Management Studio (SSMS) for easier database management.

---

## How to Run the Project

1. **Restore the Database**  
   - Locate the backup file named: `database_backup.bak`  
   - Restore it using SQL Server.

2. **Configure the Database Connection**

- In the project's configuration file (`appsettings.json`), set the server name to:  
  `" your server name"` (indicating the local SQL Server instance).  
- Alternatively, you can also manually change the server name inside **SQL Server** to `"."` to ensure proper connectivity.


3. **Open the Project**  
   - Launch Visual Studio and open the solution file.  
   - Wait a few seconds for NuGet packages to restore automatically.

4. **Run the Application**  
   - Press F5 or click Run to launch the application.

5. **Log in and Use the System**  
   You can either:
   - Register a new account through the registration page.  
   - Or use the pre-configured test account:
     - Email: `anas@gmail.com`  
     - Password: `Eelu20-00236`

---

## Important Notes

- Ensure that SQL Server is running before launching the application.
- The database must be restored before attempting to log in or use the system.

---

## Technical Details :

- The project is built using ASP.NET MVC/Core, and follows Clean Architecture principles, implementing:
  - Repository Pattern
  - Unit of Work Pattern

- Facial recognition algorithms are integrated into the system logic to analyze and match facial features with previously stored images, enabling accurate identity detection for children.
