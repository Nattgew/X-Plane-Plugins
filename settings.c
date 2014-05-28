FILE *fr;

fr = fopen ("login.txt", "rt");

if( fr == NULL) perror("Error opening settings file.\n");

fscanf(fr, "%s,%s", &PID, &Ppass);

fclose(fr);
