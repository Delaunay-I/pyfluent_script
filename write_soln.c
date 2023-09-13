#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "udf.h"

#define _CRT_SECURE_NO_WARNINGS
// #define TURB
# define FLUID_ID 6

static int iter_num = 1;


DEFINE_ON_DEMAND(write_slimSoln_onDemand)
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
            fprintf(file, "%.16Le\t%.16Le\t%.16Le", C_P(c, t), C_U(c, t), C_V(c, t));
            #endif
            #if RP_3D
            fprintf(file, "%.16Le\t%.16Le\t%.16Le\t%.16Le", C_P(c, t), C_U(c, t), C_V(c, t), C_W(c, t));
            #endif
            #ifdef TURB
            fprintf(file, "\t%.16Le\t%.16Le", C_K(c,t), C_O(c,t));
            #endif

            fprintf(file, "\n");
        }
        end_c_loop(c, t);
    }
    fclose(file);
    Message0("The solution was written to the file %s.\n", filename);
}



DEFINE_EXECUTE_AT_END(write_step_numbered)
{
    Thread *t; // Pointer to the current thread
    Domain *d = Get_Domain(1);
    cell_t c; // Cell iterator

    int n_iter = iter_num++;
    char file_number_str[32];
    snprintf(file_number_str, sizeof(file_number_str), "%d", n_iter);
    const char* base_path = "solver_data/solution_data-";
    const char* extension = ".dat";

    // Calculate the total length of the file path (including null-terminator)
    size_t path_length = strlen(base_path) + strlen(file_number_str) + strlen(extension) + 1;

    // Allocate memory for the file_path dynamically
    char* file_path = (char*)malloc(path_length);
       if (file_path == NULL) {
        printf("Memory allocation error.\n");
        return 1;
    }

    // Combine the base path and extension into file_path
    snprintf(file_path, path_length, "%s%d%s", base_path, n_iter, extension);

    FILE* file = fopen(file_path, "w");

      if (file == NULL) { // check for errors
        Message("\n Error: No write access to file %s. Abort UDF execution.\n", file_path);
        free(file_path); // Don't forget to free the allocated memory
        perror("fopen");
        return 1;
    }


    // Loop over all cell threads in the domain
    thread_loop_c(t, d)
    {
        // Loop over all cells in the current thread
        begin_c_loop(c, t)
        {
            // Get the coordinates of the cell centroid
            #if RP_2D
            fprintf(file, "%.16Le\t%.16Le\t%.16Le", C_P(c, t), C_U(c, t), C_V(c, t));
            #endif
            #if RP_3D
            fprintf(file, "%.16Le\t%.16Le\t%.16Le\t%.16Le", C_P(c, t), C_U(c, t), C_V(c, t), C_W(c, t));
            #endif
            #ifdef TURB
            fprintf(file, "\t%.16Le\t%.16Le", C_K(c,t), C_O(c,t));
            #endif
            fprintf(file, "\n");
        }
        end_c_loop(c, t)
    }

    fclose(file);
    free(file_path);
}

DEFINE_EXECUTE_AT_END(write_slimSoln_par)
{
#if !RP_HOST
    Domain *d = Get_Domain(1);
    Thread *t;
    cell_t c;
    t = Lookup_Thread(d, FLUID_ID);
#endif
#if !RP_NODE
    const char *filename = "solver_data/solution_slim.csv";
    FILE *file = fopen(filename, "w");
    if (file == NULL)
    {
        Message("\n Error: No write access to file %s. Abort UDF execution.\n", filename);
        perror("fopen");
        return 1;
    }
#endif

    int size; /* data passing variables */
    real *CP, *CU, *CV;
    #if RP_3D
    real *CW;
    #endif
    #ifdef TURB
    real *ck, *co;
    #endif
    int pe;

    /* UDF Now does 2 different things depending on NODE or HOST */
#if RP_NODE /* Each Node loads up its data passing array */
    size = THREAD_N_ELEMENTS_INT(t);
    
    CP = (real *)malloc(size * sizeof(real));
    CU = (real *)malloc(size * sizeof(real));
    CV = (real *)malloc(size * sizeof(real));
#if RP_3D
    CW = (real *)malloc(size * sizeof(real));
#endif
#ifdef TURB
    ck = (real *)malloc(size * sizeof(real));
    co = (real *)malloc(size * sizeof(real));
#endif

    begin_c_loop_int(c, t)
        CP[c] = C_P(c, t);
        CU[c] = C_U(c, t);
        CV[c] = C_V(c, t);
        #if RP_3D
        CW[c] = C_W(c, t);
        #endif
        #ifdef TURB
        ck[c] = C_K(c, t);
        co[c] = C_O(c, t);
        #endif
    end_c_loop_int(c, t)

        pe = (I_AM_NODE_ZERO_P) ? node_host : node_zero;
        PRF_CSEND_INT(pe, &size, 1, myid);
        PRF_CSEND_REAL(pe, CP, size, myid);
        PRF_CSEND_REAL(pe, CU, size, myid);
        PRF_CSEND_REAL(pe, CV, size, myid);
#if RP_3D
        PRF_CSEND_REAL(pe, CW, size, myid);
#endif
#ifdef TURB
        PRF_CSEND_REAL(pe, ck, size, myid);
        PRF_CSEND_REAL(pe, co, size, myid);
#endif
        free(CP);
        free(CU);
        free(CV);
#if RP_3D
        free(CW);
#endif
#ifdef TURB
        free(ck);
        free(co);
#endif
        /* node_0 now collect data sent by other compute nodes */
        /*  and sends it straight on to the host */
        if (I_AM_NODE_ZERO_P)
        compute_node_loop_not_zero(pe)
        {
            PRF_CRECV_INT(pe, &size, 1, pe);

//Allocating data
            CP = (real *)malloc(size * sizeof(real));
            CU = (real *)malloc(size * sizeof(real));
            CV = (real *)malloc(size * sizeof(real));
#if RP_3D
            CW = (real *)malloc(size * sizeof(real));
#endif
#ifdef TURB
            ck = (real *)malloc(size * sizeof(real));
            co = (real *)malloc(size * sizeof(real));
#endif

            // Receiving data
            PRF_CRECV_REAL(pe, CP, size, pe);
            PRF_CRECV_REAL(pe, CU, size, pe);
            PRF_CRECV_REAL(pe, CV, size, pe);
#if RP_3D
            PRF_CRECV_REAL(pe, CW, size, pe);
#endif
#ifdef TURB
            PRF_CRECV_REAL(pe, ck, size, pe);
            PRF_CRECV_REAL(pe, co, size, pe);
#endif

            // Sending to host node
            PRF_CSEND_INT(node_host, &size, 1, myid);

            PRF_CSEND_REAL(node_host, CP, size, myid);
            PRF_CSEND_REAL(node_host, CU, size, myid);
            PRF_CSEND_REAL(node_host, CV, size, myid);
#if RP_3D
            PRF_CSEND_REAL(node_host, CW, size, myid);
#endif
#ifdef TURB
            PRF_CSEND_REAL(node_host, ck, size, myid);
            PRF_CSEND_REAL(node_host, co, size, myid);
#endif

            free((char *)CP);
            free((char *)CU);
            free((char *)CV);
#if RP_3D
            free((char *)CW);
#endif
#ifdef TURB
            free((char *)ck);
            free((char *)co);
#endif
        }

#endif /* RP_NODE */
#if RP_HOST
    compute_node_loop(pe) /* only acts as a counter in this loop */
    {
        /* Receive data sent by each node and write it out to the file */
        PRF_CRECV_INT(node_zero, &size, 1, node_zero);
        //Allocating data
        CP = (real *)malloc(size * sizeof(real));
        CU = (real *)malloc(size * sizeof(real));
        CV = (real *)malloc(size * sizeof(real));
#if RP_3D
        CW = (real *)malloc(size * sizeof(real));
#endif
#ifdef TURB
        ck = (real *)malloc(size * sizeof(real));
        co = (real *)malloc(size * sizeof(real));
#endif
        // Receiving data from node-0
        PRF_CRECV_REAL(node_zero, CP, size, node_zero);
        PRF_CRECV_REAL(node_zero, CU, size, node_zero);
        PRF_CRECV_REAL(node_zero, CV, size, node_zero);
#if RP_3D
        PRF_CRECV_REAL(node_zero, CW, size, node_zero);
#endif
#ifdef TURB
        PRF_CRECV_REAL(node_zero, ck, size, node_zero);
        PRF_CRECV_REAL(node_zero, co, size, node_zero);
#endif

        for (int i = 0; i < size; i++){
            fprintf(file, "%.16Le\t%.16Le\t%.16Le", CP[i], CU[i], CV[i]);
            #if RP_3D
            fprintf(file, "\t%.16Le", CW[i]);
            #endif
            #ifdef TURB
            fprintf(file, "\t%.16Le\t%.16Le", ck[i], co[i]);
            #endif
            fprintf(file, "\n");
        }
            

        free(CP);
        free(CU);
        free(CV);
#if RP_3D
        free(CW);
#endif
#ifdef TURB
        free(ck);
        free(co);
#endif
    }
#endif /* RP_HOST */
#if !RP_NODE
    fclose(file);
#endif
}


/******************************************************************************************/
// DEFINE_EXECUTE_AT_END(write_step)
// {
//     Thread *t; // Pointer to the current thread
//     Domain *d = Get_Domain(1);
//     cell_t c; // Cell iterator

//     const char* filename = "solver_data/solution.csv";

//     FILE* file = fopen(filename, "w");

//     if (file == NULL) { // check for errors
//         Message("\n Error: No write access to file %s. Abort UDF execution.\n", filename);
//         perror("fopen");
//         return 1;
//     }

//     fprintf(file, "iter:%5d\n", iter_num++);
//     #if RP_2D
//     fprintf(file, "id\tthread_id\tp\tu\tv");
//     #endif
//     #if RP_3D
//     fprintf(file, "id\tthread_id\tp\tu\tv\tw");
//     #endif
//     #ifdef TURB
//     fprintf(file, "\tk\tomega");
//     #endif
//     fprintf(file, "\n");

//     int zone_id = -1;
//     // Loop over all cell threads in the domain
//     thread_loop_c(t, d)
//     {
//         zone_id = THREAD_ID(t);
//         // Loop over all cells in the current thread
//         begin_c_loop(c, t)
//         {
//             #if RP_2D
//             fprintf(file, "%6d\t%3d\t%.16Le\t%.16Le\t%.16Le",
//             c, zone_id,
//             C_P(c,t), C_U(c, t), C_V(c, t));
//             #endif
//             #if RP_3D
//             fprintf(file, "%6d\t%3d\t%.16Le\t%.16Le\t%.16Le\t%.16Le",
//             c, zone_id,
//             C_P(c,t), C_U(c, t), C_V(c, t), C_W(c, t));
//             #endif
//             #ifdef TURB
//             fprintf(file, "\t%.16Le\t%.16Le", C_K(c,t), C_O(c,t));
//             #endif

//             fprintf(file, "\n");
//         }
//         end_c_loop(c, t)
//     }
//     fclose(file);
// }

/******************************************************************************************/
// DEFINE_ON_DEMAND(write_HDF5)
// {
//     const char* filename = "solver_data/solution_slim.h5";
//     Thread *t;
//     cell_t c;
//     Domain *d = Get_Domain(1);


//     // Allocate memory dynamically for my_data
//     double **my_data = (double **)malloc(DIM0 * sizeof(double *));
//     for (int i = 0; i < DIM0; i++) {
//         my_data[i] = (double *)malloc(DIM1 * sizeof(double));
//     }

//     thread_loop_c(t, d)
//     {
//         begin_c_loop(c, t)
//         {
//             my_data[c][0] = C_P(c, t);
//             my_data[c][1] = C_U(c, t);
//             my_data[c][2] = C_V(c, t);
//             #if RP_3D
//             my_data[c][3] = C_W(c, t);
//             #endif
//             #ifdef TURB
//             my_data[c][4] = C_K(c, t);
//             my_data[c][5] = C_O(c, t);
//             #endif
//         }
//         end_c_loop(c, t);
//     }

//     hsize_t dims[2] = {DIM0, DIM1};
//     hid_t file = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
//     hid_t dataspace = H5Screate_simple(2, dims, NULL);
//     hid_t dataset = H5Dcreate(file, "slim_soln", H5T_NATIVE_DOUBLE, dataspace,
//                               H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
//     herr_t status = H5Dwrite(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT,
//                              my_data[0]);

//     // Clean up memory
//     status = H5Dclose(dataset);
//     status = H5Sclose(dataspace);
//     status = H5Fclose(file);

//     for (int i = 0; i < DIM0; i++)
//     {
//         free(my_data[i]);
//     }
//     free(my_data);

//     Message0("The solution was written to the file %s.\n", filename);
// }

/******************************************************************************************/
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
