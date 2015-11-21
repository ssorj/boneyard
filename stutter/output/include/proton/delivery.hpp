namespace proton {

class delivery {
  public:
    delivery() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}