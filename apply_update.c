#include <stdio.h>
#include <cassert>
#include <math.h>

#include "udf.h"

#define TURB
# define FLUID_ID 6

DEFINE_ON_DEMAND(apply_update_par)
{
#if !RP_HOST
            Domain *d = Get_Domain(1);
            Thread *t;
            cell_t c;
            t = Lookup_Thread(d, FLUID_ID);
            const char *filename = "solver_data/DMDUpdate.csv";
#endif

#if RP_NODE
    FILE* file = fopen(filename, "r");
    if (file == NULL){
        Message("ERROR: cannot open the file %s. Abort UDF execution.\n", filename);
        perror("fopen");
        return 1;
    }

    int size = THREAD_N_ELEMENTS_INT(t);
    if(I_AM_NODE_ZERO_P)
        PRF_CSEND_INT(myid + 1, &size, 1, myid);
    // Skip lines for non_zero nodes
    if (!I_AM_NODE_ZERO_P)
    {
        if (myid + 1 < compute_node_count)
            PRF_CSEND_INT(myid + 1, &size, 1, myid);
        PRF_CRECV_INT(myid - 1, &size, 1, pe);

        int linesToSkip = size;
        // Skip lines
        for (int i = 0; i < linesToSkip; i++)
        {
            char ch;
            while ((ch = fgetc(file)) != '\n' && ch != EOF){}
        }
    }

begin_c_loop_int(c, t)
        real p = 0, u = 0, v = 0;
    #if RP_2D
        fscanf(file, "%lf\t%lf\t%lf", &p, &u, &v);
    #endif
    #if RP_3D
        real w = 0;
        fscanf(file, "%lf\t%lf\t%lf\t%lf", &p, &u, &v, &w);
    #endif
    #ifdef TURB
        real k = 0, omega = 0;
        fscanf(file, "\t%lf\t%lf", &k, &omega);
    #endif
        fscanf(file, "\n");

        C_P(c, t) += p;
        C_U(c, t) += u;
        C_V(c, t) += v;
    #if RP_3D
        C_W(c, t) += w;
    #endif
    #ifdef TURB
        C_K(c, t) += k;
        C_O(c, t) += omega;
    #endif
end_c_loop_int(c, t)
#endif
}


/******************************************************************************************/
// ******************  Serial data write  *********************
// DEFINE_ON_DEMAND(apply_man_update)
// {
//     Domain *d = Get_Domain(1);
//     Thread *t;
//     cell_t c;

//     const char* filename = "solver_data/DMDUpdate.csv";

//     FILE* file = fopen(filename, "r");
//     if (file == NULL){
//         Message("ERROR: cannot open the file %s. Abort UDF execution.\n", filename);
//         perror("fopen");
//         return 1;
//     }

//     thread_loop_c(t, d)
//     {
//         /* Loop over all cells in the current thread */
//         begin_c_loop(c, t)
//         {
//             real p=0, u=0, v=0;
//             #if RP_2D
//             fscanf(file, "%lf\t%lf\t%lf", &p, &u, &v);
//             #endif
//             #if RP_3D
//             real w=0;
//             fscanf (file, "%lf\t%lf\t%lf\t%lf", &p, &u, &v, &w);
//             #endif
//             #ifdef TURB
//             real k=0, omega=0;
//             fscanf(file, "\t%lf\t%lf", &k, &omega);
//             #endif
//             fscanf(file, "\n");

//             C_P(c, t) += p;
//             C_U(c, t) += u;
//             C_V(c, t) += v;
//             #if RP_3D
//             C_W(c, t) += w;
//             #endif
//             #ifdef TURB
//             C_K(c, t) += k;
//             C_O(c, t) += omega;
//             #endif

//         }
//         end_c_loop(c, t)
//     }
//     fclose(file);
//     Message0("solution file %s applied successfully\n", filename);

// }
