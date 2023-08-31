#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "udf.h"

#define _CRT_SECURE_NO_WARNINGS
// #define TURB

static int iter_num = 1;

DEFINE_EXECUTE_AT_END(write_step)
{
    Thread *t; // Pointer to the current thread
    Domain *d = Get_Domain(1);
    cell_t c; // Cell iterator
    real x[ND_ND]; // Array to store the coordinates of the cell centroid

    const char* filename = "solver_data/solution.csv";

    FILE* file = fopen(filename, "w");

    if (file == NULL) { // check for errors
        Message("\n Error: No write access to file %s. Abort UDF execution.\n", filename);
        perror("fopen");
        return 1;
    }

    fprintf(file, "iter:%5d\n", iter_num++);
    #if RP_2D
    fprintf(file, "id\tthread_id\tp\tu\tv");
    #endif
    #if RP_3D
    fprintf(file, "id\tthread_id\tp\tu\tv\tw");
    #endif
    #ifdef TURB
    fprintf(file, "\tk\tomega");
    #endif
    fprintf(file, "\n");

    int zone_id = -1;
    // Loop over all cell threads in the domain
    thread_loop_c(t, d)
    {
        zone_id = THREAD_ID(t);
        // Loop over all cells in the current thread
        begin_c_loop(c, t)
        {
            // Get the coordinates of the cell centroid
            C_CENTROID(x, c, t);
            #if RP_2D
            fprintf(file, "%6d\t%3d\t%.16Le\t%.16Le\t%.16Le",
            c, zone_id,
            C_P(c,t), C_U(c, t), C_V(c, t));
            #endif
            #if RP_3D
            fprintf(file, "%6d\t%3d\t%.16Le\t%.16Le\t%.16Le\t%.16Le",
            c, zone_id,
            C_P(c,t), C_U(c, t), C_V(c, t), C_W(c, t));
            #endif
            #ifdef TURB
            fprintf(file, "\t%.16Le\t%.16Le", C_K(c,t), C_O(c,t));
            #endif

            fprintf(file, "\n");
        }
        end_c_loop(c, t)
    }
    fclose(file);
}


DEFINE_ON_DEMAND(write_slimUpdate_onDemand)
{
    const char* filename = "solver_data/solution_slim.csv";
    Thread *t;
    cell_t c;
    Domain *d = Get_Domain(1);

    FILE *file = fopen(filename, "w");

    if (file == NULL) {
        Message("\n Error: No write access to file %s. Abort UDF execution.\n", filename);
        perror("fopen");
        return 1;
    }

    thread_loop_c(t, d)
    {
        begin_c_loop(c, t)
        {
            #if RP_2D
            fprintf(file, "%.16Le\t%.16Le\t%.16Le\n", C_P(c, t), C_U(c, t), C_V(c, t));
            #endif
            #if RP_3D
            fprintf(file, "%.16Le\t%.16Le\t%.16Le\t%.16Le\n", C_P(c, t), C_U(c, t), C_V(c, t), C_W(c, t));
            #endif
        }
        end_c_loop(c, t);
    }
    fclose(file);
    Message0("The solution was written to the file %s.\n", filename);
}



// DEFINE_EXECUTE_AT_END(write_step_numbered)
// {
//     Thread *t; // Pointer to the current thread
//     Domain *d = Get_Domain(1);
//     cell_t c; // Cell iterator
//     real x[ND_ND]; // Array to store the coordinates of the cell centroid

//     int n_iter = iter_num++;
//     char file_number_str[32];
//     snprintf(file_number_str, sizeof(file_number_str), "%d", n_iter);
//     const char* base_path = "./solution_data-";
//     const char* extension = ".dat";

//     // Calculate the total length of the file path (including null-terminator)
//     size_t path_length = strlen(base_path) + strlen(file_number_str) + strlen(extension) + 1;

//     // Allocate memory for the file_path dynamically
//     char* file_path = (char*)malloc(path_length);
//        if (file_path == NULL) {
//         printf("Memory allocation error.\n");
//         return 1;
//     }

//     // Combine the base path and extension into file_path
//     snprintf(file_path, path_length, "%s%d%s", base_path, n_iter, extension);

//     FILE* file = fopen(file_path, "w");

//       if (file == NULL) { // check for errors
//         Message("\n Error: No write access to file %s. Abort UDF execution.\n", file_path);
//         free(file_path); // Don't forget to free the allocated memory
//         perror("fopen");
//         return 1;
//     }

//     #if RP_2D
//     fprintf(file, "id\tthread_id\tx\ty\trho\tp\tu\tv\tk\tomega\n");
//     #endif
//     #if RP_3D
//     fprintf(file, "id\tthread_id\tx\ty\trho\tp\tu\tv\tw\tk\tomega\n");
//     #endif

//     // Loop over all cell threads in the domain
//     thread_loop_c(t, d)
//     {
//         // Loop over all cells in the current thread
//         begin_c_loop(c, t)
//         {
//             // Get the coordinates of the cell centroid
//             C_CENTROID(x, c, t);
//             #if RP_2D
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], C_R(c, t), C_U(c, t), C_V(c, t));
//             #endif
//             #if RP_3D
//             fprintf(file, "%10.5e\\t%10.5e\\t%10.5e\\t%10.5e\\t%10.5e\\t%10.5e\\t%10.5e\\n", x[0], x[1], x[2], C_R(c, t), C_U(c, t), C_V(c, t), C_W(c, t));
//             #endif
//         }
//         end_c_loop(c, t)
//     }

//     fclose(file);
//     free(file_path);

// }


// DEFINE_EXECUTE_AT_END(write_step_vec)
// {
//     Thread *t;
//     Domain *d = Get_Domain(1);
//     cell_t c; 
//     real x[ND_ND];

//     const char* filename = "solution_vec.dat";

//     FILE* file = fopen(filename, "w");

//     if (file == NULL) { // check for errors
//         Message("\n Error: No write access to file %s. Abort UDF execution.\n", filename);
//         perror("fopen");
//         return 1;
//     }

//     #if RP_2D
//     fprintf(file, "id\tthread_id\tx\ty\trho\tp\tu\tv\tk\tomega\n");
//     #endif
//     #if RP_3D
//     fprintf(file, "id\tthread_id\tx\ty\trho\tp\tu\tv\tw\tk\tomega\n");
//     #endif

//     // Loop over all cell threads in the domain
//     thread_loop_c(t, d)
//     {
//         // Loop over all cells in the current thread
//         begin_c_loop(c, t)
//         {
//             // Get the coordinates of the cell centroid
//             C_CENTROID(x, c, t);
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], C_P(c, t));
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], C_U(c, t));
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], C_V(c, t));
//             #if RP_3D
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], x[2], C_R(c, t));
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], x[2], C_U(c, t));
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], x[2], C_V(c, t));
//             fprintf(file, "%10.5e\t%10.5e\t%10.5e\t%10.5e\n", x[0], x[1], x[2], C_W(c, t));
//             #endif
//         }
//         end_c_loop(c, t)
//     }

//     fclose(file);

// }
