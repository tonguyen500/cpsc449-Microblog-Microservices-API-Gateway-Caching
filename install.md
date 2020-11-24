# Install Instructions
1. Unzip Tar file:
*	Cd into directory containing the tar file 
*	Run command 
`$ tar -xvf FILE.tar`  
 Where FILE is the name of the file you want to un-tar

2. Cd into the project directory and Download necessary files with  
	`$ sudo apt update`  
	`$ sudo apt install –yes python3-pip`  
	`$ sudo apt install python3-flask`  
	`$ sudo apt install ruby-foreman`  
	`$ sudo apt install httpie`  

3. Run these commands to initialize the database  
	`$ export FLASK_APP=user_api.py`  
	`$ flask init`  

 

